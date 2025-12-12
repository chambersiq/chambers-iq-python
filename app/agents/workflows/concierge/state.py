from typing import TypedDict, List, Optional, Any, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class ConciergeState(TypedDict):
    """State for the AI Assistant / Concierge workflow."""
    messages: Annotated[List[BaseMessage], add_messages]
    company_id: str
    user_email: str
    
    # Context
    active_client_id: Optional[str]
    active_case_id: Optional[str]
    
    # Internal
    next_step: Optional[str]
