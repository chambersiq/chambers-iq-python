from typing import TypedDict, List, Optional, Dict, Any

class LegalWorkflowState(TypedDict):
    """
    Represents the state of the legal template generation workflow.
    """
    thread_id: str
    sample_docs: List[str]
    template: Optional[str]
    template_approved: bool
    attorney_feedback: Optional[str]
    case_variables: Optional[Dict[str, Any]]
    final_document: Optional[str]
    status: str
    current_step: str
    is_simulation: bool
    revision_summary: Optional[str]
