from typing import TypedDict, List, Dict, Optional, Any

class LegalWorkflowState(TypedDict):
    """
    Legacy state for Template Architect Workflow.
    Preserved to avoid breaking existing import references.
    """
    # Inputs
    sample_docs: List[str]
    user_instructions: Optional[str]
    is_simulation: bool
    
    # Generated Outputs
    template: Optional[str]
    case_variables: Optional[Dict[str, Any]]
    final_document: Optional[str]
    
    # Workflow Control
    status: str # "processing", "awaiting_attorney_review", "completed", "error"
    current_step: str
    
    # Feedback Loop
    attorney_feedback: Optional[str]
    revision_summary: Optional[str]
    template_approved: bool
