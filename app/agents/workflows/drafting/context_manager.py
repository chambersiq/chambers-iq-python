from app.agents.workflows.drafting.state import DraftState
from app.agents.workflows.drafting.schema import FactEntry, DraftedSection
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

class DraftContextManager:
    def __init__(self, llm=None):
        self.llm = llm

    async def initialize_context(self, state: DraftState) -> dict:
        """
        Agent Node: Initialize global context (Facts, Summaries) before drafting starts.

        This extracts facts from:
        1. Case metadata (caseSummary, keyFacts, etc.)
        2. Document AI summaries (aiSummary, extractedData)
        3. Template variables (to identify what's needed)
        """
        print("--- [ContextManager] Initializing Context ---")

        case_data = state.get("case_data", {})
        documents = state.get("documents", [])
        template_data = state.get("template_data", {})

        # Initialize registries
        fact_registry = {}
        document_summaries = {}

        # Step 1: Extract facts from Case metadata
        if case_data:
            # Case identifiers
            if case_data.get("caseNumber"):
                fact_registry["case_number"] = FactEntry(
                    key="case_number",
                    value=case_data["caseNumber"],
                    source_document="case_metadata",
                    source_page=None,
                    confidence=1.0,
                    used_in_sections=[],
                    last_updated=datetime.now()
                )

            # Court details
            if case_data.get("courtName"):
                fact_registry["court_name"] = FactEntry(
                    key="court_name",
                    value=case_data["courtName"],
                    source_document="case_metadata",
                    confidence=1.0,
                    used_in_sections=[],
                    last_updated=datetime.now()
                )

            if case_data.get("jurisdiction"):
                fact_registry["jurisdiction"] = FactEntry(
                    key="jurisdiction",
                    value=case_data["jurisdiction"],
                    source_document="case_metadata",
                    confidence=1.0,
                    used_in_sections=[],
                    last_updated=datetime.now()
                )

            # Parties
            if case_data.get("clientName"):
                fact_registry["petitioner_name"] = FactEntry(
                    key="petitioner_name",
                    value=case_data["clientName"],
                    source_document="case_metadata",
                    confidence=1.0,
                    used_in_sections=[],
                    last_updated=datetime.now()
                )

            if case_data.get("opposingPartyName"):
                fact_registry["respondent_name"] = FactEntry(
                    key="respondent_name",
                    value=case_data["opposingPartyName"],
                    source_document="case_metadata",
                    confidence=1.0,
                    used_in_sections=[],
                    last_updated=datetime.now()
                )

            # Case summary and strategy
            if case_data.get("caseSummary"):
                fact_registry["case_summary"] = FactEntry(
                    key="case_summary",
                    value=case_data["caseSummary"],
                    source_document="case_metadata",
                    confidence=1.0,
                    used_in_sections=[],
                    last_updated=datetime.now()
                )

            if case_data.get("clientPosition"):
                fact_registry["client_position"] = FactEntry(
                    key="client_position",
                    value=case_data["clientPosition"],
                    source_document="case_metadata",
                    confidence=1.0,
                    used_in_sections=[],
                    last_updated=datetime.now()
                )

            if case_data.get("prayer"):
                fact_registry["prayer"] = FactEntry(
                    key="prayer",
                    value=case_data["prayer"],
                    source_document="case_metadata",
                    confidence=1.0,
                    used_in_sections=[],
                    last_updated=datetime.now()
                )

            # Key facts from array
            if case_data.get("keyFacts"):
                for idx, fact in enumerate(case_data["keyFacts"]):
                    fact_registry[f"key_fact_{idx}"] = FactEntry(
                        key=f"key_fact_{idx}",
                        value=fact,
                        source_document="case_metadata",
                        confidence=1.0,
                        used_in_sections=[],
                        last_updated=datetime.now()
                    )

        # Step 2: Process uploaded documents
        for doc in documents:
            doc_id = doc.get("documentId", "unknown")

            # Store document summary
            if doc.get("aiStatus") == "completed" and doc.get("aiSummary"):
                document_summaries[doc_id] = {
                    "filename": doc.get("name", "unknown"),
                    "type": doc.get("type", "unknown"),
                    "summary": doc.get("aiSummary", ""),
                    "extracted_data": doc.get("extractedData"),
                    "s3_key": doc.get("s3Key"),
                    "url": doc.get("url")
                }

                # Try to extract structured facts from extractedData
                if doc.get("extractedData"):
                    extracted = doc["extractedData"]
                    # Store specialist analysis as facts
                    if extracted.get("specialistAnalysis"):
                        fact_key = f"doc_{doc_id}_analysis"
                        fact_registry[fact_key] = FactEntry(
                            key=fact_key,
                            value=extracted["specialistAnalysis"],
                            source_document=doc.get("name", "unknown"),
                            confidence=0.9,  # AI extracted
                            used_in_sections=[],
                            last_updated=datetime.now()
                        )
            else:
                # Document not processed yet
                print(f"Document {doc.get('name')} not processed (aiStatus: {doc.get('aiStatus')})")

        print(f"Initialized {len(fact_registry)} facts from case and {len(document_summaries)} document summaries")

        return {
            "fact_registry": fact_registry,
            "document_summaries": document_summaries,
            "section_memory": [],
            "consistency_index": {}
        }

    async def get_section_context(self, state: DraftState, section: Any) -> Dict[str, Any]:
        """
        Provide focused context for drafting a specific section.

        Returns:
        - required_facts: Dict of facts needed for this section
        - previous_sections: Last 2-3 drafted sections
        - related_documents: Document summaries relevant to this section
        - case_context: Case summary, position, prayer
        - consistency_warnings: Any detected conflicts
        - missing_facts: Facts that couldn't be found
        """
        fact_registry = state.get("fact_registry", {})
        section_memory = state.get("section_memory", [])
        document_summaries = state.get("document_summaries", {})
        case_data = state.get("case_data", {})

        # Get required facts for this section
        # CRITICAL FIX: Also inspect template for placeholders, don't just rely on static plan
        import re
        template_vars = re.findall(r'\{(\w+)\}', getattr(section, 'template_text', ''))
        
        # Merge lists (deduplicate)
        all_needed_keys = set(section.required_facts) | set(template_vars)
        
        required_facts = {}
        missing_facts = []

        for fact_key in all_needed_keys:
            if fact_key in fact_registry:
                fact_entry = fact_registry[fact_key]
                required_facts[fact_key] = {
                    "value": fact_entry.value,
                    "source": fact_entry.source_document,
                    "confidence": fact_entry.confidence
                }
            else:
                missing_facts.append({
                    "key": fact_key,
                    "status": "MISSING",
                    "suggestion": "Check documents or request from user"
                })

        # Get previous sections (last 2-3)
        previous_sections = []
        for prev_section in section_memory[-3:]:
            previous_sections.append({
                "section_id": prev_section.section_id,
                "title": getattr(prev_section, 'title', 'Unknown'),
                "content_excerpt": prev_section.content[:200] if len(prev_section.content) > 200 else prev_section.content,
                "facts_used": prev_section.facts_used
            })

        # Get related documents (all for now, could be filtered by relevance)
        related_documents = [
            {
                "doc_id": doc_id,
                "filename": summary["filename"],
                "type": summary["type"],
                "summary": summary["summary"],
                "url": summary.get("url")
            }
            for doc_id, summary in document_summaries.items()
        ]

        # Build case context
        case_context = {
            "case_summary": case_data.get("caseSummary", ""),
            "client_position": case_data.get("clientPosition", ""),
            "key_facts": case_data.get("keyFacts", []),
            "prayer": case_data.get("prayer", ""),
            "case_type": case_data.get("caseType", state.get("case_type", ""))
        }

        return {
            "required_facts": required_facts,
            "previous_sections": previous_sections,
            "related_documents": related_documents,
            "case_context": case_context,
            "consistency_warnings": [],  # TODO: Implement consistency checking
            "missing_facts": missing_facts
        }

    async def store_drafted_section(self, state: DraftState, drafted_section: DraftedSection) -> dict:
        """
        Store a completed section in section memory and update fact usage.
        """
        section_memory = state.get("section_memory", [])
        fact_registry = state.get("fact_registry", {})

        # Add to section memory
        section_memory.append(drafted_section)

        # Update fact usage tracking
        for fact_key in drafted_section.facts_used:
            if fact_key in fact_registry:
                fact_registry[fact_key].used_in_sections.append(drafted_section.section_id)

        print(f"Stored section {drafted_section.section_id} in memory")

        return {
            "section_memory": section_memory,
            "fact_registry": fact_registry
        }

    async def process_human_feedback(self, state: DraftState) -> dict:
        """
        Process human feedback to update the Fact Registry.
        This consolidates knowledge management in the Context Manager.
        """
        print("--- [ContextManager] Processing Human Feedback ---")
        
        feedback = state.get("human_feedback")
        fact_registry = state.get("fact_registry", {})
        
        if not feedback:
            print("  No feedback to process")
            return {}

        # Use LLM to extract facts
        print(f"  Extracting facts from: '{feedback[:50]}...'")
        
        # We need to import system messages locally or at top
        from langchain_core.messages import SystemMessage, HumanMessage
        import json
        import re

        system_prompt = """You are a Legal Fact Extractor.
Your goal is to extract structured facts from human feedback and update the Fact Registry.

Input:
1. Current Fact Registry (JSON)
2. Human Feedback (Text)

Output:
JSON dict of NEW or UPDATED facts (key-value pairs).
Ignore feedback that is purely instructional (e.g., "rewrite this", "make it shorter") unless it contains factual data.

Format:
{
  "court_name": "Delhi High Court",
  "marriage_date": "2015-03-10"
}

If no facts are present, return {}.
"""
        
        def get_fact_value(v):
            if isinstance(v, dict):
                return v.get('value', 'unknown')
            if hasattr(v, 'value'):
                return v.value
            return str(v)

        existing_facts_summary = {k: get_fact_value(v) for k, v in list(fact_registry.items())[:20]}
        
        user_msg = f"""Current Registry Sample:
{json.dumps(existing_facts_summary, indent=2)}

Human Feedback:
"{feedback}"

Extract facts:"""

        try:
            # Re-use the LLM initialized in __init__
            if not self.llm:
                # Fallback if init didn't provide it
                from app.agents.workflows.drafting.llm_utils import create_cached_llm
                from app.core.config import settings
                self.llm = create_cached_llm(model=settings.LLM_MODEL, provider=settings.LLM_PROVIDER)

            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_msg)
            ])
            
            content = response.content
            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                new_facts = json.loads(json_match.group())
                
                if new_facts:
                    print(f"  ✓ Extracted {len(new_facts)} new facts: {list(new_facts.keys())}")
                    
                    # Update registry
                    for k, v in new_facts.items():
                        fact_registry[k] = FactEntry(
                            key=k,
                            value=v,
                            source_document="human_feedback", # Updated source name
                            confidence=1.0,
                            used_in_sections=[],
                            last_updated=datetime.now()
                        )
                    
                    return {
                        "fact_registry": fact_registry,
                        "workflow_logs": state.get("workflow_logs", []) + [{
                            "agent": "ContextManager", # Log as ContextManager
                            "message": f"Extracted facts from feedback: {', '.join(new_facts.keys())}",
                            "timestamp": "now"
                        }]
                    }
                else:
                    print("  No new facts found in feedback")
                    return {
                         "workflow_logs": state.get("workflow_logs", []) + [{
                            "agent": "ContextManager",
                            "message": "Processed guidance (no new facts extracted)",
                            "timestamp": "now"
                        }]
                    }
            
        except Exception as e:
            print(f"  ⚠️ Extraction failed: {e}")

        return {}

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

# Runnable/Node wrapper
context_manager = DraftContextManager()

async def context_init_node(state: DraftState):
    return await context_manager.initialize_context(state)

async def feedback_processing_node(state: DraftState):
    return await context_manager.process_human_feedback(state)
