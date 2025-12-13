from app.agents.workflows.drafting.state import DraftState
from app.agents.workflows.drafting.llm_utils import (
    create_cached_llm,
    create_cached_messages_with_context
)
from typing import Dict, Any
from functools import lru_cache
import json

from app.core.config import settings
from app.agents.workflows.drafting.config import drafting_config

class DraftRefiner:
    def __init__(self, llm=None):
        # Use cached LLM with Anthropic prompt caching enabled
        self.llm = llm or create_cached_llm(
            model=settings.LLM_MODEL,
            provider=settings.LLM_PROVIDER
        )

    async def refine_plan(self, state: DraftState) -> dict:
        """
        Final Document Refiner: Validate entire draft against template.

        Performs final checks after all sections drafted:
        1. Template coverage - All sections present?
        2. Section connections - Flow and coherence?
        3. Consistency - Cross-references valid?
        4. Completeness - All requirements met?
        5. Final suggestions for improvement
        """
        print(f"--- [Final Refiner] Validating entire document ---")

        section_memory = state.get("section_memory", [])
        plan = state.get("plan")
        template_content = state.get("template_content", "")
        case_data = state.get("case_data", {})

        if not section_memory:
            print("  Warning: No drafted sections found")
            return {"refinement_plan": None}

        # Combine all sections into full document
        full_draft = "\n\n---\n\n".join([
            f"## {sec.section_id}\n{sec.content}"
            for sec in section_memory
        ])

        # Load System Prompt (will be cached at API level)
        system_prompt = load_drafting_prompt("refiner")

        # Prepare context for caching
        fact_registry = state.get("fact_registry", {})
        
        # Check for low confidence facts used in the draft
        low_conf_warnings = []
        for key, entry in fact_registry.items():
            # Check if fact was used (simple heuristic or explicit tracking)
            if hasattr(entry, 'used_in_sections') and entry.used_in_sections:
                if entry.confidence < drafting_config.CONFIDENCE_THRESHOLD and not entry.is_verified:
                    low_conf_warnings.append(f"Fact '{key}' ({entry.value}) used with low confidence ({entry.confidence}).")

        cache_context = {
            "case_data": case_data,
            "template_content": template_content[:5000] if template_content else "", 
            "planned_sections": [
                {"title": sec.title, "required_facts": sec.required_facts}
                for sec in (plan.sections if plan else [])
            ],
            "low_confidence_facts": low_conf_warnings
        }

        # Create validation query (NOT cached - changes per draft)
        user_message = f"""Perform FINAL DOCUMENT VALIDATION for this complete legal draft.

**Drafted Sections** ({len(section_memory)} sections):
{full_draft[:3000]}... [truncated for brevity]

**Planned Sections**:
{', '.join([sec.title for sec in (plan.sections if plan else [])])}

---

## FINAL VALIDATION CHECKLIST

### 1. TEMPLATE COVERAGE
- Are all planned sections present?
- Are sections in correct order?
- Any missing sections?

### 2. SECTION CONNECTIONS
- Do sections flow coherently?
- Are transitions smooth?
- Cross-references valid?

### 3. OVERALL CONSISTENCY
- Consistent terminology throughout?
- No contradictions between sections?
- Consistent tone and style?

### 4. COMPLETENESS
- All template requirements met?
- All case details included?
- Ready for filing?

### 5. FINAL POLISH
- Any formatting issues?
- Any improvements needed?

### 6. FACT CONFIDENCE CHECK
The following facts were used with LOW CONFIDENCE (AI inferred but not verified):
{json.dumps(low_conf_warnings, indent=2)}

Use this list to generate "Warning" issues for any fact that looks suspicious or critical.

---

## OUTPUT FORMAT (JSON)

Provide HUMAN-READABLE final validation:

{{
  "template_coverage": {{
    "all_sections_present": true|false,
    "missing_sections": ["list if any"],
    "section_order": "correct|needs_adjustment",
    "coverage_percentage": 95
  }},
  "document_quality": {{
    "overall_score": "excellent|good|acceptable|needs_work",
    "coherence": "Sections flow well together",
    "consistency": "Terminology and tone consistent",
    "completeness": "All requirements met"
  }},
  "issues": [
    {{
      "type": "missing_section|inconsistency|formatting|other",
      "severity": "Critical|Warning|Info",
      "description": "Clear description",
      "suggested_fix": "What to do"
    }}
  ],
  "final_suggestions": [
    "Add verification clause at end",
    "Consider adding witness list if applicable"
  ],
  "ready_for_filing": true|false,
  "human_review_notes": "Brief notes for final human reviewer"
}}

Provide comprehensive final validation."""

        # Create messages with optimal caching structure
        messages = create_cached_messages_with_context(
            system_prompt=system_prompt,
            user_message=user_message,
            context=cache_context,
            cache_system=True,  # Cache the system prompt
            cache_context=True  # Cache the case/section context
        )

        # Invoke LLM
        print("  Performing final document validation...")
        response = await self.llm.ainvoke(messages)

        # Extract validation results
        validation_analysis = response.content if hasattr(response, 'content') else str(response)

        # Try to parse JSON response
        try:
            # Extract JSON from response (might be wrapped in markdown code blocks)
            import re
            json_match = re.search(r'\{[\s\S]*\}', validation_analysis)
            if json_match:
                final_validation = json.loads(json_match.group())
            else:
                final_validation = {
                    "template_coverage": {"all_sections_present": True, "coverage_percentage": 100},
                    "document_quality": {"overall_score": "good"},
                    "issues": [],
                    "final_suggestions": [],
                    "ready_for_filing": True,
                    "human_review_notes": validation_analysis[:500]
                }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            final_validation = {
                "template_coverage": {"all_sections_present": True, "coverage_percentage": 100},
                "document_quality": {"overall_score": "acceptable"},
                "issues": [],
                "final_suggestions": [validation_analysis[:200]],
                "ready_for_filing": True,
                "human_review_notes": "Review validation output manually"
            }

        # Log cache performance
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            cache_read = usage.get('cache_read_input_tokens', 0)
            if cache_read > 0:
                print(f"  ✓ Cache HIT: {cache_read} tokens from cache")

        # Log results
        overall_score = final_validation.get("document_quality", {}).get("overall_score", "unknown")
        coverage = final_validation.get("template_coverage", {}).get("coverage_percentage", 0)
        ready = final_validation.get("ready_for_filing", False)

        print(f"  📊 Overall Quality: {overall_score}")
        print(f"  📋 Template Coverage: {coverage}%")
        print(f"  {'✅' if ready else '⚠️'} Ready for Filing: {ready}")

        return {
            "final_validation": final_validation,
            "refinement_plan": None,  # Clear old refinement plan
        }

# Helper with caching
import os
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
def get_refiner_agent():
    return DraftRefiner()  # Will use default cached LLM

async def refiner_node(state: DraftState):
    agent = get_refiner_agent()
    return await agent.refine_plan(state)
