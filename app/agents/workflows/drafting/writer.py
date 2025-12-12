from app.agents.workflows.drafting.state import DraftState
from app.agents.workflows.drafting.schema import DraftedSection, SectionStatus, Citation
from app.agents.workflows.drafting.context_manager import context_manager
from app.agents.workflows.drafting.citation_agent import citation_agent
from app.agents.workflows.drafting.llm_utils import (
    create_cached_llm,
    create_cached_messages_with_context
)
import uuid
import re
import os
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
        print("--- [Writer] Drafting Section ---")

        plan = state.get("plan")
        current_idx = state.get("current_section_idx", 0)

        if not plan or current_idx >= len(plan.sections):
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
            # TODO: Implement actual citation agent query
            # For now, create placeholder citations
            for law_query in section.required_laws:
                citations.append(Citation(
                    text=f"Reference to {law_query}",
                    source="Indian Kanoon",
                    url="https://indiankanoon.org/",
                    case_name=None,
                    year=None
                ))
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
        system_prompt = load_drafting_prompt("writer")

        # Prepare context for caching (static per case)
        cache_context = {
            "template": section.template_text,
            "case_data": state.get("case_data", {}),
            "documents": state.get("documents", []),
            "previous_sections": context["previous_sections"],
            "required_facts": context["required_facts"]
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
        
        if reviewer_feedback and not human_feedback:
             # Only show reviewer feedback if no direct human override, or show both? 
             # Usually human feedback is "Fix X", which implies they saw the review.
             # Let's show both contextually.
             feedback_text += f"\n\n**Previous Reviewer Feedback**:\n{reviewer_feedback}\n"

        user_message = f"""Draft the following section:

**Section Title**: {section.title}

**Required Facts**: {', '.join(section.required_facts) if section.required_facts else 'None'}

**Required Laws**: {', '.join(section.required_laws) if section.required_laws else 'None'}
{citations_text}
{missing_facts_text}
{feedback_text}

**Instructions**:
1. Use the template structure provided in the context
2. Fill all placeholders with facts from the fact registry OR from the "CRITICAL INSTRUCTION FROM HUMAN" section
3. Use formal Indian legal language appropriate for {context["case_context"].get("case_type", "legal document")}
4. Integrate citations naturally into the text
5. Mark missing facts as [MISSING: key] ONLY if they are not in the registry AND not provided in human instructions
6. Maintain consistency with previously drafted sections
7. Ensure all factual statements are traceable to the fact registry or explicitly provided instructions
8. IF HUMAN FEEDBACK IS PROVIDED, YOU MUST INCORPORATE IT. Prioritize human instructions over registry missing flags.

Please draft this section now."""

        # Create messages with optimal caching structure
        messages = create_cached_messages_with_context(
            system_prompt=system_prompt,
            user_message=user_message,
            context=cache_context,
            cache_system=True,  # Cache the system prompt
            cache_context=True  # Cache the case/template/docs context
        )

        # Invoke LLM (will use cached content if available within 5-minute window)
        response = await self.llm.ainvoke(messages)

        # Extract draft content
        draft_content = response.content if hasattr(response, 'content') else str(response)

        # Log cache performance if available
        if hasattr(response, 'usage_metadata'):
            usage = response.usage_metadata
            cache_read = usage.get('cache_read_input_tokens', 0)
            cache_create = usage.get('cache_creation_input_tokens', 0)
            input_tokens = usage.get('input_tokens', 0)

            if cache_read > 0:
                print(f"  ✓ Cache HIT: {cache_read} tokens read from cache (90% savings)")
            elif cache_create > 0:
                print(f"  ⚡ Cache MISS: {cache_create} tokens written to cache (available for 5 minutes)")

            print(f"  📊 Tokens: {input_tokens} input, {usage.get('output_tokens', 0)} output")

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
