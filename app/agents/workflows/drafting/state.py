from typing import TypedDict, List, Dict, Optional, Any, Annotated
from datetime import datetime
import operator
from app.agents.workflows.drafting.schema import (
    DraftingPlan,
    FactEntry,
    DraftedSection,
    QAReport,
    RefinementPlan,
    Section
)

class DraftState(TypedDict):
    """
    Global state for the Multi-Agent Drafting Workflow.
    Passed between all nodes in the LangGraph.
    """

    # --- Case & Project Metadata ---
    case_id: str
    case_type: str
    client_id: str
    company_id: str
    template_id: Optional[str]
    created_at: str # ISO string

    # --- Case Data (from Case model) ---
    case_data: Optional[Dict[str, Any]]  # Full Case object as dict

    # --- Documents (from DocumentService) ---
    documents: Optional[List[Dict[str, Any]]]  # List of Document objects

    # --- Template Data ---
    template_content: Optional[str]  # HTML/text template with placeholders
    template_data: Optional[Dict[str, Any]]  # Full Template object

    # --- Planning State ---
    plan: Optional[DraftingPlan]
    current_section_idx: int
    completed_section_ids: List[str]

    # --- Document & Context Intelligence (Oracle) ---
    document_summaries: Dict[str, str] # doc_id -> summary
    fact_registry: Dict[str, FactEntry] # key -> FactEntry check schema.py
    section_memory: List[DraftedSection]  # Previously drafted sections
    consistency_index: Dict[str, Dict[str, Any]]  # Track entity mentions across sections

    # --- Current Section Execution State ---
    current_section: Optional[Section]
    current_section_context: Optional[Dict[str, Any]]  # Context provided to Writer
    current_draft: Optional[DraftedSection]
    current_qa_report: Optional[QAReport]

    # --- Final Assembly ---
    final_document_content: Optional[str]
    final_document_url: Optional[str] # S3 link

    # --- Human Feedback & Control Flow ---
    human_feedback: Optional[str]
    human_readable_feedback: Optional[str] # Feedback from Reviewer to Human
    human_verdict: Optional[str] # "approve", "reject", "refine"
    refinement_plan: Optional[RefinementPlan]
    draft_preview: Optional[str]  # Cleaning draft content for human display
    workflow_logs: List[Dict[str, str]] # structured logs: {agent, message, timestamp}
    iteration_count: int # Safety to prevent infinite loops
    max_iterations: int  # Default: 3
    section_redraft_count: Optional[int]  # Track redrafts per section (for loop prevention, defaults to 0)
    error: Optional[str]
