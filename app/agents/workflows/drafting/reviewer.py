from app.agents.workflows.drafting.state import DraftState
from app.agents.workflows.drafting.schema import QAReport, QAStatus, Issue
from app.agents.workflows.drafting.llm_utils import (
    create_cached_llm,
    create_cached_messages_with_context
)
import re
import os
import json
from datetime import datetime
from typing import List, Dict, Any
from functools import lru_cache

class DraftReviewer:
    def __init__(self, llm=None):
        # Use cached LLM with Anthropic prompt caching enabled
        # Use cached LLM with configured provider
        from app.core.config import settings
        self.llm = llm or create_cached_llm(
            model=settings.LLM_MODEL,
            provider=settings.LLM_PROVIDER
        )

    async def review_section(self, state: DraftState) -> dict:
        """
        Agent Node: Review the current draft using LLM-based comprehensive validation.

        Uses LLM to perform all validation checks:
        - Structural (placeholders, format, completeness)
        - Factual (consistency with fact registry)
        - Legal (citations validity, Indian legal standards)
        - Semantic (coherence, tone, reasoning quality)
        """
        print("--- [Reviewer] Reviewing Draft with LLM ---")

        draft = state.get("current_draft")
        if not draft:
            return {"error": "No draft to review"}

        current_section = state.get("current_section")
        fact_registry = state.get("fact_registry", {})
        section_memory = state.get("section_memory", [])

        print(f"  Reviewing section: {current_section.title if current_section else 'Unknown'}")
        print(f"  [DEBUG] Reviewing content (first 100 chars): {draft.content[:100].replace(chr(10), ' ')}...")

        # Perform comprehensive LLM validation
        issues = await self._validate_with_llm(draft, current_section, fact_registry, section_memory, state)

        # Determine status based on issues
        critical_issues = [i for i in issues if i.severity == "Critical"]
        warnings = [i for i in issues if i.severity == "Warning"]

        if critical_issues:
            status = QAStatus.FAIL
            recommendation = f"Redraft required - {len(critical_issues)} critical issue(s) found"
        elif warnings:
            status = QAStatus.PASS_WITH_WARNINGS
            recommendation = f"Proceed to human review - {len(warnings)} warning(s) present"
        else:
            status = QAStatus.PASS
            recommendation = "Approve - Ready for human review"

        report = QAReport(
            section_id=draft.section_id,
            status=status,
            issues=issues,
            recommendation=recommendation
        )

        print(f"  ✓ QA Status: {status.value} ({len(critical_issues)} critical, {len(warnings)} warnings)")

        # Clean the draft content for display (remove technical markers)
        cleaned_content = self._clean_draft_for_display(draft.content) if draft else ""

        # Update logs
        logs = state.get("workflow_logs", [])
        log_entry = {
            "agent": "Reviewer",
            "message": f"Reviewed section '{current_section.title if current_section else 'Unknown'}': {status.value} ({len(critical_issues)} critical, {len(warnings)} warnings).",
            "timestamp": datetime.now().isoformat()
        }
        # Counter will be incremented by routing logic if needed
        return {
            "current_qa_report": report,
            "human_readable_feedback": self._format_human_readable_feedback(report, issues),
            "draft_preview": cleaned_content,  # Clean version for display to humans
            "workflow_logs": logs
        }

    def _format_human_readable_feedback(self, report: QAReport, issues: List[Issue]) -> str:
        """
        Format QA report into concise, human-readable feedback.
        Focuses on actionable items, especially for human review cases.
        """
        lines = []

        # Critical issues - most important, keep it simple
        critical = [i for i in issues if i.severity == "Critical"]
        if critical:
            lines.append("**Please provide the following missing details:**")
            lines.append("")
            for idx, issue in enumerate(critical, 1):
                # Extract just the key information
                lines.append(f"{idx}. {issue.description}")
                if issue.suggested_fix and issue.suggested_fix != issue.description:
                    lines.append(f"   → {issue.suggested_fix}")
            lines.append("")

        # Warnings - secondary priority
        warnings = [i for i in issues if i.severity == "Warning"]
        if warnings and len(warnings) <= 3:  # Only show if not too many
            lines.append("**Additional improvements needed:**")
            for idx, issue in enumerate(warnings, 1):
                lines.append(f"• {issue.description}")
            lines.append("")

        # If no critical issues, show status
        if not critical:
            if report.status.value == "PASS":
                lines.append("✓ Section approved")
            elif report.status.value == "PASS_WITH_WARNINGS":
                lines.append("⚠️  Section approved with minor improvements suggested")

        return "\n".join(lines).strip()

    def _clean_draft_for_display(self, content: str) -> str:
        """
        Clean draft content for human display by removing technical markers.

        Removes:
        - [MISSING: key] markers
        - [CITE] markers
        - Other technical annotations

        Returns a clean version suitable for human review.
        """
        import re

        # Remove [MISSING: ...] markers
        cleaned = re.sub(r'\[MISSING:\s*[^\]]+\]', '[...]', content)

        # Remove [CITE] markers
        cleaned = re.sub(r'\[CITE\]', '', cleaned)

        # Remove other technical markers [PLACEHOLDER: ...]
        cleaned = re.sub(r'\[PLACEHOLDER:\s*[^\]]+\]', '[...]', cleaned)

        # Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Clean up spaces around [...]
        cleaned = re.sub(r'\s*\[\.\.\.\]\s*', ' [...] ', cleaned)

        return cleaned.strip()

    async def _validate_with_llm(self, draft: Any, section: Any, fact_registry: Dict, section_memory: List, state: DraftState) -> List[Issue]:
        """
        Comprehensive LLM-based validation.

        Performs all validation checks:
        1. Structural: Placeholders, format, completeness
        2. Factual: Consistency with fact registry, no contradictions
        3. Legal: Citations validity, Indian legal standards compliance
        4. Semantic: Coherence, tone, reasoning quality
        5. Completeness: All required elements present
        """
        issues = []

        # Load system prompt (will be cached at API level)
        system_prompt = load_drafting_prompt("reviewer")

        # Prepare context for caching (static per case)
        # Handle fact_registry - it might be a dict or list
        if isinstance(fact_registry, dict):
            fact_registry_sample = {k: v.value if hasattr(v, 'value') else v for k, v in list(fact_registry.items())[:20]}
        else:
            fact_registry_sample = {}  # Fallback if not a dict

        cache_context = {
            "case_data": state.get("case_data", {}),
            "case_type": state.get("case_type", "unknown"),
            "template": getattr(section, 'template_text', '') if section else '',
            "section_title": getattr(section, 'title', 'Unknown') if section else 'Unknown',
            "fact_registry": fact_registry_sample,  # Limit to 20 facts to save tokens
            "required_facts": getattr(section, 'required_facts', []) if section else [],
            "required_laws": getattr(section, 'required_laws', []) if section else []
        }

        # Create validation query (NOT cached - changes per draft)
        feedback_block = ""
        human_feedback = state.get("human_feedback")
        human_readable_feedback = state.get("human_readable_feedback")

        if human_feedback:
            feedback_block = f"""
---
## CRITICAL CONTEXT: HUMAN FEEDBACK
The human user explicitly provided this feedback/instruction:
"{human_feedback}"

**INSTRUCTION FOR REVIEWER**:
- If the draft incorporates this human feedback, it is CORRECT.
- IGNORE discrepancies with the Fact Registry if they align with this human feedback.
- Do NOT flag "missing facts" if the human explicitly provided them here.
---
"""

        user_message = f"""Perform comprehensive validation of this drafted section and provide HUMAN-READABLE feedback.

**Section Title**: {cache_context['section_title']}

**Draft Content**:
{draft.content}

**Facts Used**: {', '.join(draft.facts_used[:10])}

**Citations**: {len(draft.citations_used)} citation(s) included

**Word Count**: {draft.word_count} words
{feedback_block}
---

## CRITICAL: EXTRACT INFORMATION, DON'T COPY MARKERS

The draft above may contain technical markers like:
- [MISSING: court_name]
- [CITE]
- [PLACEHOLDER: xyz]

**DO NOT copy these markers into your output!**

Instead, EXTRACT the information and report it cleanly:
- If you see "[MISSING: court_name]" → Report: "Court name is missing"
- If you see "[MISSING: case_number]" → Report: "Case number is not provided"
- If you see "[CITE]" → Report: "Citation reference needs to be filled"

---

## IMPORTANT: HUMAN-READABLE OUTPUT

Your feedback will be shown to HUMAN REVIEWERS. Make it:
- **Clear and concise**: No technical jargon or markers
- **Actionable**: Tell them exactly what to fix
- **Organized**: Group related issues together
- **Professional**: Respectful tone

**Examples**:
❌ BAD: "Found [MISSING: court_name] in title section"
❌ BAD: "Title contains [MISSING: court_name] marker"
✅ GOOD: "Court name is missing"
✅ GOOD: "Please provide the court name"

---

## COMPREHENSIVE VALIDATION CHECKLIST

### 1. STRUCTURAL VALIDATION (Critical Issues)
- ✓ Check for unfilled placeholders: Any {{variable}} remaining?
- ✓ Check for [MISSING: key] markers: Are facts missing?
- ✓ Word count reasonable: Too short (< 20 words) or suspiciously long?
- ✓ Content not empty: Is there actual content?
- ✓ Format correct: Proper structure and formatting?

### 2. FACTUAL CONSISTENCY (Critical Issues)
- ✓ Facts match registry: Do stated facts align with provided case data?
- ✓ No contradictions: Any conflicts with previous sections?
- ✓ No fabricated facts: Are all facts traceable to case data?
- ✓ Fact usage correct: Are facts used in the right context?

### 3. LEGAL COMPLIANCE (Critical/Warning Issues)
- ✓ Indian legal language: Appropriate formal language for Indian courts?
- ✓ Citations properly integrated: Natural integration, not forced?
- ✓ Citation markers filled: No [CITE] markers left unfilled?
- ✓ Required legal provisions: All necessary laws/cases cited?
- ✓ Legal drafting standards: Follows Indian legal document conventions?
- ✓ Case type appropriateness: Suitable for {cache_context['case_type']}?

### 4. SEMANTIC QUALITY (Warning/Info Issues)
- ✓ Coherence: Logically structured and flows naturally?
- ✓ Consistency: No internal contradictions?
- ✓ Clarity: Easy to understand and unambiguous?
- ✓ Reasoning quality: Sound legal reasoning?

### 5. STYLE & TONE (Warning/Info Issues)
- ✓ Formal language: Consistently formal and professional?
- ✓ Tone appropriateness: Assertive but respectful?
- ✓ No casual phrases: Avoid informal language?
- ✓ Proper terminology: Correct legal terms used?

### 6. COMPLETENESS (Critical/Warning Issues)
- ✓ Required elements present: All mandatory components included?
- ✓ Template coverage: All template requirements addressed?
- ✓ Section requirements met: Fulfills section objectives?

---

## OUTPUT FORMAT (JSON)

Provide your analysis as JSON with HUMAN-READABLE descriptions:

{{
  "issues": [
    {{
      "type": "missing_fact|unfilled_placeholder|inconsistency|invalid_citation|semantic|style|completeness|formatting",
      "severity": "Critical|Warning|Info",
      "description": "Human-readable description (e.g., 'Missing court name', NOT 'Found [MISSING: court_name]')",
      "location": "Specific location (e.g., 'Title section', 'Line 3')",
      "suggested_fix": "What to do (e.g., 'Provide the court name where petition will be filed')"
    }}
  ],
  "overall_assessment": "Brief, professional summary for human reviewer (1-2 sentences)",
  "quality_score": "excellent|good|acceptable|needs_improvement|poor",
  "strengths": ["2-3 key strengths in simple language"],
  "must_fix": ["Critical issues in simple terms - what needs to be done"]
}}

**Example of GOOD human-readable issues**:
{{
  "issues": [
    {{
      "type": "missing_fact",
      "severity": "Critical",
      "description": "Court name is missing",
      "location": "Title section",
      "suggested_fix": "Please provide the name of the court where this petition will be filed"
    }},
    {{
      "type": "missing_fact",
      "severity": "Critical",
      "description": "Case number placeholder not filled",
      "location": "Title section",
      "suggested_fix": "Provide the case number or remove the placeholder if not yet assigned"
    }}
  ],
  "overall_assessment": "Draft has proper structure but missing 2 critical details needed for filing.",
  "quality_score": "needs_improvement",
  "strengths": ["Clear party identification", "Proper formal language"],
  "must_fix": ["Court name", "Case number"]
}}

---

## IMPORTANT GUIDELINES

1. **Severity Levels**:
   - **Critical**: Blocks approval (unfilled placeholders, missing facts, fabricated data, major legal errors)
   - **Warning**: Should fix but not blocking (minor legal issues, style inconsistencies)
   - **Info**: Nice to improve (suggestions for enhancement)

2. **Be Precise**: Reference specific text, not general observations

3. **Be Helpful**: Provide actionable fixes, not just criticisms

4. **Be Realistic**: Only report genuine issues, not nitpicks

5. **Context Matters**: Consider this is for {cache_context['case_type']} in Indian legal context

Now perform the comprehensive validation."""

        # Create messages with optimal caching structure
        messages = create_cached_messages_with_context(
            system_prompt=system_prompt,
            user_message=user_message,
            context=cache_context,
            cache_system=True,  # Cache the system prompt
            cache_context=True  # Cache the case/section context
        )

        try:
            # Invoke LLM
            response = await self.llm.ainvoke(messages)
            llm_analysis = response.content if hasattr(response, 'content') else str(response)

            # Log cache performance
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                cache_read = usage.get('cache_read_input_tokens', 0)
                if cache_read > 0:
                    print(f"    ✓ Cache HIT: {cache_read} tokens from cache")

            # Parse JSON response
            json_match = re.search(r'\{[\s\S]*\}', llm_analysis)
            if json_match:
                validation_result = json.loads(json_match.group())

                # Convert LLM issues to Issue objects
                for llm_issue in validation_result.get('issues', []):
                    issues.append(Issue(
                        type=llm_issue.get('type', 'semantic'),
                        description=llm_issue.get('description', ''),
                        location=llm_issue.get('location', 'Unknown'),
                        severity=llm_issue.get('severity', 'Info'),
                        suggested_fix=llm_issue.get('suggested_fix', '')
                    ))

                # Log overall assessment and quality score
                if validation_result.get('overall_assessment'):
                    quality_score = validation_result.get('quality_score', 'unknown')
                    print(f"    📊 Quality Score: {quality_score}")
                    print(f"    💬 Assessment: {validation_result['overall_assessment'][:120]}...")

                # Log must-fix issues if any
                must_fix = validation_result.get('must_fix', [])
                if must_fix:
                    print(f"    ⚠️  Must Fix: {len(must_fix)} critical issue(s)")

        except Exception as e:
            print(f"    ⚠️  LLM validation failed: {str(e)}")
            print(f"    ℹ️  This is a system error, not a draft quality issue")
            # Return empty issues list - workflow can continue but user should check logs
            return []

        return issues

# Helper with caching
from app.agents.workflows.drafting.cache import cache_prompt

@cache_prompt
def load_drafting_prompt(filename: str) -> str:
    """Load system prompt with automatic caching."""
    path = os.path.join(os.path.dirname(__file__), f"../../prompts/system_prompts/drafting/{filename}.md")
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return "You are an expert legal assistant."

@lru_cache
def get_reviewer_agent():
    return DraftReviewer()

async def reviewer_node(state: DraftState):
    agent = get_reviewer_agent()
    return await agent.review_section(state)
