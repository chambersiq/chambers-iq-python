from app.agents.workflows.drafting.state import DraftState
from app.agents.workflows.drafting.schema import FactEntry, FactResolution, ResolutionResult, DraftedSection
from app.agents.workflows.drafting.llm_utils import create_cached_messages_with_context
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.workflows.drafting.config import drafting_config
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
import html
import re
import json
from app.services.core.case_service import CaseService
from app.services.core.document_service import DocumentService
from app.services.core.template_service import TemplateService
from app.agents.workflows.drafting.cache import cache_content

# Right after imports
print(f"DEBUG: Module level - FactEntry imported: {FactEntry}")
print(f"DEBUG: Module level - FactEntry type: {type(FactEntry)}")

class DraftContextManager:
    def __init__(self, llm=None):
        self.llm = llm

    async def initialize_context(self, state: DraftState) -> dict:
        """
        Agent Node: Initialize global context (Facts, Summaries) before drafting starts.
        """
        # Ensure data is loaded if not already present (failsafe)
        if not state.get("case_data"):
            print("  [ContextManager] Data not pre-loaded, loading now...")
            data_update = await self.load_initial_data(state)
            if "error" in data_update:
                return data_update
            # Update local vars from the loaded data
            state.update(data_update)

        return await self._extract_facts_and_summaries(state)

    @cache_content(ttl=300)
    async def _load_case_data(self, company_id: str, case_id: str):
        case_service = CaseService()
        case = case_service.get_case_by_id(company_id, case_id)
        return case.model_dump() if case else None

    @cache_content(ttl=300)
    async def _load_template_data(self, company_id: str, template_id: str):
        template_service = TemplateService()
        template = template_service.get_template(company_id, template_id)
        if template:
            return {
                "data": template.model_dump(),
                "content": template.content
            }
        return None

    async def _load_documents_lazy(self, company_id: str, case_id: str, limit: int = None):
        document_service = DocumentService()
        documents = document_service.get_documents(company_id, case_id)
        # Filter to AI processed docs
        completed_docs = [doc for doc in documents if doc.aiStatus == "completed"]
        # Sort by newest
        completed_docs.sort(key=lambda x: x.createdAt, reverse=True)
        if limit:
            completed_docs = completed_docs[:limit]
        return [doc.model_dump() for doc in completed_docs]

    async def load_initial_data(self, state: DraftState) -> dict:
        """
        Centralized data loading. Called by the first node in the graph.
        """
        print("--- [ContextManager] Loading Initial Data ---")
        case_id = state.get("case_id")
        company_id = state.get("company_id")
        template_id = state.get("template_id")
        
        if not case_id or not company_id:
            print(f"  [Error] Missing ID: case={case_id}, company={company_id}")
            return {"error": "Missing case_id or company_id"}

        # Load Case
        case_data = await self._load_case_data(company_id, case_id)
        if not case_data:
            return {"error": f"Case {case_id} not found"}
        
        print(f"  Loaded case: {case_data.get('caseName', 'Unknown')}")

        # Load Documents (Lazy)
        documents_data = await self._load_documents_lazy(company_id, case_id, limit=10)
        print(f"  Loaded {len(documents_data)} documents")

        # Load Template
        template_content = ""
        template_data = None
        if template_id:
            template_result = await self._load_template_data(company_id, template_id)
            if template_result:
                template_data = template_result["data"]
                # Sanitize loaded template content
                template_content = self._sanitize_input(template_result["content"])
                print(f"  Loaded template: {template_data.get('name', 'Unknown')}")

            if template_result:
                template_data = template_result["data"]
                # Sanitize loaded template content
                template_content = self._sanitize_input(template_result["content"])
                print(f"  Loaded template: {template_data.get('name', 'Unknown')}")
                
                # Ensure description is available
                template_description = template_data.get("description", "")
        
        return {
            "case_data": case_data,
            "documents": documents_data,
            "template_content": template_content,
            "template_data": template_data,
            "template_description": template_description if template_id else "",
            "case_type": case_data.get("caseType", "unknown")
        }

    async def _extract_facts_and_summaries(self, state: DraftState) -> dict:
        """
        Refactored logic for fact extraction (was in initialize_context).
        """
        print("--- [ContextManager] Initializing Facts & Memories ---")

        case_data = state.get("case_data", {})
        documents = state.get("documents", [])
        template_data = state.get("template_data", {})

        # Initialize registries
        fact_registry = {}
        document_summaries = {}

        # Step 1: Extract facts from Case metadata (Comprehensive)
        if case_data:
            # Dynamic mapping of common case fields to fact keys
            # Add more mappings here as needed
            field_mappings = {
                'caseNumber': 'case_number',
                'courtName': 'court_name',
                'jurisdiction': 'jurisdiction',
                'clientName': 'petitioner_name',
                'opposingPartyName': 'respondent_name',
                'caseSummary': 'case_summary',
                'clientPosition': 'client_position', 
                'prayer': 'prayer',
                'judgeName': 'judge_name',
                'filingDate': 'filing_date',
                'caseType': 'case_type'
            }
            
            for field, fact_key in field_mappings.items():
                if case_data.get(field):
                    fact_registry[fact_key] = FactEntry(
                        key=fact_key,
                        value=case_data[field],
                        source_document="case_metadata",
                        confidence=1.0,
                        used_in_sections=[],
                        last_updated=datetime.now()
                    )

            # Extract any other scalar string fields from case_data as fallback
            # This ensures we capture custom fields provided by the backend
            for k, v in case_data.items():
                if isinstance(v, str) and k not in field_mappings and v:
                     # Convert camelCase to snake_case for the key
                     snake_key = re.sub(r'(?<!^)(?=[A-Z])', '_', k).lower()
                     if snake_key not in fact_registry:
                         fact_registry[snake_key] = FactEntry(
                            key=snake_key,
                            value=v,
                            source_document="case_metadata_autodetect",
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

        # Sanitize feedback
        feedback = self._sanitize_input(feedback)
        
        # Use LLM to extract facts
        print(f"  Extracting facts from: '{feedback[:50]}...'")
        
        # We need to import system messages locally or at top
        from langchain_core.messages import SystemMessage, HumanMessage
        import json
        import re

        # Prepare extraction prompt based on context
        resolution_result = state.get("resolution_result")
        
        if resolution_result and resolution_result.human_input_needed:
             # Targeted extraction: We know what keys the human is providing
             missing_keys_str = ", ".join(resolution_result.human_input_needed)
             task_context = f"The user is specifically providing values for these missing keys: {missing_keys_str}. Focus extraction on these."
        else:
             # Generice extraction
             task_context = "Extract all factual information provided."

        system_prompt = f"""You are a Legal Fact Extractor.
Your goal is to extract structured facts from human feedback and update the Fact Registry.

Context:
{task_context}

Input:
1. Current Fact Registry (JSON)
2. Human Feedback (Text)

Output:
JSON dict of NEW or UPDATED facts (key-value pairs).
Ignore feedback that is purely instructional (e.g., "rewrite this", "make it shorter") unless it contains factual data.

Format:
{{
  "court_name": "Delhi High Court",
  "marriage_date": "2015-03-10"
}}

If no facts are present, return {{}}.
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
                    
                    # Update registry with Human Facts
                    for k, v in new_facts.items():
                        fact_registry[k] = FactEntry(
                            key=k,
                            value=v,
                            source_document="human_feedback",
                            confidence=1.0, # Human is truth
                            used_in_sections=[],
                            last_updated=datetime.now()
                        )
                        
                    # Also merge auto-resolved facts if they exist
                    if resolution_result:
                         print(f"  ✓ Merging {len(resolution_result.resolved_facts)} auto-resolved facts.")
                         for res in resolution_result.resolved_facts:
                              # Only add if human didn't override it
                              if res.key not in new_facts:
                                  fact_registry[res.key] = FactEntry(
                                    key=res.key,
                                    value=res.value,
                                    source_document=f"AI_Inference ({res.confidence})",
                                    confidence=res.confidence,
                                    used_in_sections=[],
                                    last_updated=datetime.now()
                                )

                    return {
                        "fact_registry": fact_registry,
                        "resolution_result": None, # Clear partial state
                        "workflow_logs": state.get("workflow_logs", []) + [{
                            "agent": "ContextManager", 
                            "message": f"Updated registry with {len(new_facts)} human facts + auto-resolutions.",
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

    async def resolve_missing_info(self, missing_keys: List[str], state: DraftState) -> ResolutionResult:
        """
        Smart Resolution Engine:
        Attempts to deduce missing facts from available context (Case Data + Documents)
        using LLM inference before bothering the human user.
        """
        print(f"--- [ContextManager] Smart Resolution for {len(missing_keys)} keys ---")

        # Pre-check: Don't resolve facts we already have with high confidence
        fact_registry = state.get("fact_registry", {})
        truly_missing = []
        for key in missing_keys:
            existing = fact_registry.get(key)
            if not existing or existing.confidence < 0.8:
                truly_missing.append(key)
            else:
                print(f"  ✓ Skipping {key}: Already loaded with confidence {existing.confidence}")
        
        if not truly_missing:
             print("  ✓ All keys already present in registry. Skipping LLM.")
             return ResolutionResult(resolved_facts=[], human_input_needed=[], rag_context_used=[])

        missing_keys = truly_missing
        
        # 1. Gather rich context
        context_str = self._gather_complete_context(state)
        
        # 2. Prepare Prompt
        system_prompt = load_drafting_prompt("smart_resolver")
        
        user_msg = f"""Missing Information Keys:
{json.dumps(missing_keys, indent=2)}

Available Context:
{context_str}

**Task**:
For each missing key, attempt to infer the value from the context.
- Assign a confidence score (0.0 - 1.0).
- If confidence >= {drafting_config.CONFIDENCE_THRESHOLD}, it will be auto-resolved.
- If confidence < {drafting_config.CONFIDENCE_THRESHOLD}, we will ask the human.

Provide output in JSON format matching the FactResolution schema."""

        # 3. LLM Inference
        # Helper to ensure LLM is ready
        if not self.llm:
            from app.agents.workflows.drafting.llm_utils import create_cached_llm
            from app.core.config import settings
            self.llm = create_cached_llm(model=settings.LLM_MODEL, provider=settings.LLM_PROVIDER)

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_msg)
            ])
            
            # 4. Parse & Process Results
            content = response.content
            json_match = re.search(r'\{[\s\S]*\}', content)
            
            resolved_facts = []
            human_needed = []
            
            if json_match:
                data = json.loads(json_match.group())
                # Expecting data to be a list of FactResolution or a dict with a list
                resolutions = data.get("resolutions", [])
                
                for res in resolutions:
                    # Robust handling
                    if not isinstance(res, dict):
                         continue
                    
                    try:
                        row = FactResolution(**res)
                        if row.confidence >= drafting_config.CONFIDENCE_THRESHOLD:
                            # High confidence -> Auto-resolve
                            print(f"  ✓ Auto-resolved: {row.key} = {row.value} (Conf: {row.confidence})")
                            resolved_facts.append(row)
                        else:
                            # Low confidence -> Flag for human
                            print(f"  ? Needs Human: {row.key} (Conf: {row.confidence})")
                            human_needed.append(row.key)
                    except Exception as parse_err:
                        print(f"  ⚠️ Failed to parse resolution item: {parse_err}")
                
                # Check for keys that were skipped entirely by LLM
                processed_keys = set(r['key'] for r in resolutions)
                for k in missing_keys:
                    if k not in processed_keys:
                        human_needed.append(k)

                return ResolutionResult(
                    resolved_facts=resolved_facts,
                    human_input_needed=list(set(human_needed)), # Dedupe
                    rag_context_used=[]
                )

        except Exception as e:
            print(f"  ⚠️ Smart Resolution Failed: {e}")
            # Fallback: All missing keys need human input
            return ResolutionResult(
                resolved_facts=[],
                human_input_needed=missing_keys,
                rag_context_used=[]
            )

        return ResolutionResult(resolved_facts=[], human_input_needed=missing_keys, rag_context_used=[])

    def _gather_complete_context(self, state: DraftState) -> str:
        """Aggregate all available context for inference."""
        parts = []
        
        # Case Data
        if state.get("case_data"):
             parts.append(f"CASE DATA:\n{json.dumps(state['case_data'], indent=2)}")
             
        # Documents (Summaries & partial text inferred)
        # In a real RAG system, we'd query vector DB here. 
        # For now, we use loaded doc dumps which might be large, so we truncate.
        docs = state.get("documents", [])
        if docs:
            doc_context = ""
            for d in docs[:drafting_config.Initial_DOC_LIMIT]: 
                doc_context += f"- Title: {d.get('title')}\n  Type: {d.get('documentType')}\n  Summary: {d.get('aiSummary')}\n"
            parts.append(f"DOCUMENTS (Top {drafting_config.Initial_DOC_LIMIT}):\n{doc_context}")
            
        return "\n\n".join(parts)

    def _update_fact_registry(self, state: DraftState, resolution: FactResolution) -> dict:
        """Helper to write inferred fact to registry and return state update."""
        print(f"DEBUG: _update_fact_registry called with key={resolution.key}")
        print(f"DEBUG: FactEntry imported? {FactEntry is not None}")
        print(f"DEBUG: FactEntry in globals? {'FactEntry' in globals()}")
        
        registry = state.get("fact_registry", {})
        print(f"DEBUG: registry has {len(registry)} items")
        
        # Try creating FactEntry
        try:
            entry = FactEntry(
                key=resolution.key,
                value=resolution.value,
                source_document=f"AI_Inference ({resolution.confidence})", # Correct field
                confidence=resolution.confidence,
                used_in_sections=[],
                last_updated=datetime.now()
            )
            print(f"DEBUG: FactEntry created successfully: {entry.key}")
            registry[resolution.key] = entry
            return {"fact_registry": registry}
        except Exception as e:
            print(f"DEBUG: FactEntry creation failed: {e}")
            raise



    def _sanitize_input(self, text: str) -> str:
        """
        Basic sanitization to prevent injection attacks and handling logical issues.
        Escapes HTML chars and limits length.
        """
        if not text:
            return ""
        
        # Limit length to prevent context window DoS
        MAX_LEN = 100000 
        if len(text) > MAX_LEN:
            print(f"  ⚠️ Warning: Input text truncated from {len(text)} to {MAX_LEN} chars")
            text = text[:MAX_LEN]
            
        # Basic HTML escaping
        return html.escape(text)



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
