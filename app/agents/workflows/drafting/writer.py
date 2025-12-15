from app.agents.workflows.drafting.state import DraftState
from app.agents.workflows.drafting.schema import DraftedSection, SectionStatus, Citation
from app.agents.workflows.drafting.context_manager import context_manager
from app.agents.workflows.drafting.citation_agent import get_citation_agent
from app.agents.workflows.drafting.llm_utils import (
    create_cached_llm,
    create_cached_messages_with_context
)
from app.agents.workflows.drafting.logger import drafting_logger
import uuid
import re
import os
import json
import time  # Added missing import
from typing import Dict, List, Any
from functools import lru_cache

class DraftWriter:
    def __init__(self, llm=None):
        # Use cached LLM with Anthropic prompt caching enabled
        # Use cached LLM with configured provider
        from app.core.config import settings
        self.llm = llm or create_cached_llm(
            model=settings.LLM_MODEL,
            provider=settings.LLM_PROVIDER
        )

    async def write_section(self, state: DraftState) -> dict:
        """
        Agent Node: Draft the current section.

        Process:
        1. Get current section from plan
        2. Query Context Manager for facts and context
        3. Query Citation Agent for legal references (if needed)
        4. Generate draft using LLM
        5. Fill placeholders and create final section
        """
        workflow_id = state.get("workflow_id", "unknown")
        section_idx = state.get("current_section_idx", 0)

        drafting_logger.log_agent_start("writer", workflow_id, section_idx)
        print("--- [Writer] Drafting Section ---")

        plan = state.get("plan")
        current_idx = state.get("current_section_idx", 0)

        if not plan or current_idx >= len(plan.sections):
             drafting_logger.log_error(workflow_id, "writer", "no_section_to_draft", "No section to draft")
             drafting_logger.log_agent_end("writer", workflow_id, "error", section_idx=section_idx)
             return {"error": "No section to draft"}

        section = plan.sections[current_idx]
        print(f"Drafting: {section.title} (Section {current_idx + 1}/{len(plan.sections)})")

        # Step 1: Query Context Manager for section context
        print("  [1/3] Gathering context from Context Manager...")
        section_context = await context_manager.get_section_context(state, section)

        # Step 2: Query Citation Agent if legal references are needed
        citations = []
        if section.required_laws:
            print(f"  [2/3] Querying Citation Agent for {len(section.required_laws)} legal references...")
            citation_agent = get_citation_agent()
            
            # Query for each required law
            for law_query in section.required_laws:
                try:
                    print(f"    Researching: {law_query}...")
                    # Perform actual research
                    research_result = await citation_agent.perform_research(f"Find legal details and precedents for: {law_query}")
                    
                    citations.append(Citation(
                        text=research_result[:1500], # Limit text length
                        source="Indian Kanoon (AI Research)",
                        url="https://indiankanoon.org/", # Default, ideally extracted from research
                        case_name=None,
                        year=None
                    ))
                except Exception as e:
                    print(f"    ⚠️ Research failed for '{law_query}': {str(e)}")
        else:
            print("  [2/3] No legal references needed, skipping Citation Agent")

        # Step 3: Generate draft content with LLM (using API-level prompt caching)
        print("  [3/3] Generating draft content with cached LLM...")
        draft_content = await self._generate_draft(section, section_context, citations, state)

        # Fill placeholders in the template
        filled_placeholders = self._fill_placeholders(section.template_text, section_context["required_facts"])

        # Create the drafted section
        draft = DraftedSection(
            section_id=section.id,
            content=draft_content,
            facts_used=list(section_context["required_facts"].keys()),
            citations_used=citations,
            placeholders_filled=filled_placeholders,
            word_count=len(draft_content.split())
        )

        print(f"✓ Drafted {draft.word_count} words, used {len(draft.facts_used)} facts")

        # Log section completion
        drafting_logger.log_writer_output(
            workflow_id=workflow_id,
            section_idx=section_idx,
            section_title=section.title,
            word_count=draft.word_count,
            facts_used=len(draft.facts_used),
            citations_used=len(draft.citations_used),
            placeholders_filled=draft.placeholders_filled
        )

        drafting_logger.log_agent_end("writer", workflow_id, "success", section_idx=section_idx)

        return {
            "current_draft": draft,
            "current_section_context": section_context,
            "current_section": section
        }

    async def _generate_draft(self, section: Any, context: Dict, citations: List[Citation], state: DraftState) -> str:
        """
        Generate the actual draft content using LLM with API-level prompt caching.

        Uses Anthropic's prompt caching to cache:
        1. System prompt (writer instructions) - 90% cost reduction
        2. Case data, documents, template - 90% cost reduction
        3. Dynamic query (section-specific) - NOT cached

        This structure provides 48-66% overall cost savings on multi-section documents.
        """
        # Load system prompt (will be cached at API level)
        # system_prompt = load_drafting_prompt("writer") # Original system prompt

        # Add Template Context
        if state.get("template_id"):
            # We need to fetch the template details here or trust they are in state
            # For simplicity, assuming the state might key template details or we fetch
            # Ideally, the `orchestrator` or `context_manager` fetched it.
            pass

        template_content = state.get("template_content", "")
        template_description = state.get("template_description", "")

        # Enhanced feedback inclusion for redrafts
        human_feedback = state.get("human_feedback")
        reviewer_feedback = state.get("human_readable_feedback")

        print(f"  📝 Writer Feedback Context:")
        print(f"     - Human feedback: {human_feedback[:100] if human_feedback else 'None'}...")
        print(f"     - Reviewer feedback: {reviewer_feedback[:100] if reviewer_feedback else 'None'}...")

        # Build comprehensive feedback section
        feedback_section = ""
        if reviewer_feedback:
            feedback_section = f"""

**🔴 CRITICAL REVIEWER FEEDBACK - MUST ADDRESS ALL POINTS:**
{reviewer_feedback}

**REDRAFT INSTRUCTIONS:**
- Carefully read all reviewer feedback above
- Address every issue and requirement mentioned
- Fill ALL missing placeholders using the case data
- Fix any content quality or legal compliance issues
- Ensure the draft meets all specified standards
"""

        if human_feedback:
            feedback_section += f"""

**👤 HUMAN FEEDBACK - HIGHEST PRIORITY:**
{human_feedback}
"""

        system_prompt = f"""You are an expert legal drafter specializing in Indian legal documents.

TASK: Draft a legal document section based on the provided context.

TEMPLATE CONTEXT:
The user has selected a specific template.
Template Content:
{template_content}

Template Guidance (Description):
{template_description}

{feedback_section}
        """

        # Prepare context for caching (static per case)
        cache_context = {
            "template": section.template_text,
            "case_data": state.get("case_data", {}),
            "template_data": state.get("template_data", {}), # Contains usageInstructions
            "documents": state.get("documents", []),
            "previous_sections": context["previous_sections"],
            "required_facts": context["required_facts"],
            "full_fact_registry": state.get("fact_registry", {})  # ADD THIS for context awareness
        }

        # Create section-specific query (NOT cached - changes per section)
        citations_text = ""
        if citations:
            citations_text = "\n\nAvailable Citations:\n" + "\n".join([
                f"- {cit.text} ({cit.source})"
                for cit in citations
            ])

        missing_facts_text = ""
        if context["missing_facts"]:
            missing_facts_text = "\n\nMissing Facts (mark as [MISSING: key]):\n" + "\n".join([
                f"- {fact['key']}: {fact.get('suggestion', '')}"
                for fact in context["missing_facts"]
            ])

        feedback_text = ""
        human_feedback = state.get("human_feedback")
        reviewer_feedback = state.get("human_readable_feedback")

        if human_feedback:
             feedback_text += f"\n\n**CRITICAL INSTRUCTION FROM HUMAN (MUST FOLLOW)**:\n{human_feedback}\n"
             # Explicit override instruction
             feedback_text += "**HUMAN FEEDBACK PRIORITY**: If human provided values above, use them INSTEAD OF registry values.\n"
             feedback_text += 'Example: If human says "Court name - Delhi High Court", use "Delhi High Court" even if registry has different value.\n'
        
        if reviewer_feedback and not human_feedback:
             # Only show reviewer feedback if no direct human override, or show both? 
             # Usually human feedback is "Fix X", which implies they saw the review.
             # Let's show both contextually.
             feedback_text += f"\n\n**Previous Reviewer Feedback**:\n{reviewer_feedback}\n"
             
        # Template Usage Instructions
        template_data = state.get("template_data", {})
        usage_instructions = template_data.get("usageInstructions")
        if usage_instructions:
            feedback_text += f"\n\n**TEMPLATE USAGE INSTRUCTIONS**:\n{usage_instructions}\n"

        # Prepare available facts JSON for prompt
        full_registry = state.get("fact_registry", {})
        # Convert to simple dict of values
        fact_values = {k: v.value if hasattr(v, 'value') else v for k, v in full_registry.items()}
        
        user_message = f"""**Complete Case Information:**
{json.dumps(state.get("case_data", {}), indent=2)}

**Document Summaries:**
{json.dumps(state.get("document_summaries", {}), indent=2)}

{feedback_section}

**Section to Draft:**
Title: {section.title}
Template: {section.template_text}

**Instructions:**
1. Using the Complete Case Information above, fill ALL placeholders ({{variable}}, äävariableåå, etc.) in the section template
2. Map case data intelligently:
   - {{court_state}} → Extract state from jurisdiction/location data
   - {{court_location}} → Use court name + jurisdiction
   - {{case_number}} → Use the case number from case data
   - {{case_year}} → Extract year from filing date
   - {{petitioner_name}} → Use client name
   - {{respondent_name}} → Use opposing party name
3. Do NOT leave any placeholders unfilled - use the case data to determine appropriate values
4. Address all reviewer feedback provided above
5. Use formal Indian legal language appropriate for matrimonial disputes
6. Integrate any citations naturally if provided
7. Ensure content is legally accurate and complete

Draft this section now:"""

        # Create messages with optimal caching structure
        messages = create_cached_messages_with_context(
            system_prompt=system_prompt,
            user_message=user_message,
            context=cache_context,
            cache_system=True,  # Cache the system prompt
            cache_context=True  # Cache the case/template/docs context
        )

        # Invoke LLM (will use cached content if available within 5-minute window)
        start_time = time.time()
        response = await self.llm.ainvoke(messages)
        duration_ms = int((time.time() - start_time) * 1000)

        # Extract draft content
        draft_content = response.content if hasattr(response, 'content') else str(response)

        # Log LLM call with performance metrics
        workflow_id = state.get("workflow_id", "unknown")
        section_idx = state.get("current_section_idx", 0)

        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            cache_read = usage.get('cache_read_input_tokens', 0)
            cache_create = usage.get('cache_creation_input_tokens', 0)
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)

            from app.core.config import settings
            drafting_logger.log_llm_call(
                workflow_id=workflow_id,
                agent_name="writer",
                model=settings.LLM_MODEL,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_create,
                duration_ms=duration_ms,
                section_idx=section_idx
            )

            if cache_read > 0:
                print(f"  ✓ Cache HIT: {cache_read} tokens read from cache (90% savings)")
            elif cache_create > 0:
                print(f"  ⚡ Cache MISS: {cache_create} tokens written to cache (available for 5 minutes)")

            print(f"  📊 Tokens: {input_tokens} input, {output_tokens} output")

        return draft_content

    def _fill_placeholders(self, template: str, facts: Dict[str, Any]) -> Dict[str, str]:
        """
        Track which placeholders were filled with what values.
        """
        filled = {}
        placeholders = re.findall(r'\{(\w+)\}', template)

        for placeholder in placeholders:
            if placeholder in facts:
                filled[placeholder] = str(facts[placeholder]["value"])
            else:
                filled[placeholder] = f"[MISSING]"

        return filled

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
def get_writer_agent():
    return DraftWriter()

async def writer_node(state: DraftState):
    agent = get_writer_agent()
    return await agent.write_section(state)
