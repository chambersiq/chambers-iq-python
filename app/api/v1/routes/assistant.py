from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from app.api.v1.dependencies import get_current_user_email, get_current_company_id
from app.agents.workflows.concierge.graph import app as concierge_app
from langchain_core.messages import HumanMessage, AIMessage

router = APIRouter()
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    threadId: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    threadId: str

# In-memory storage for simple conversation history (if not using checkpointer yet)
# ideally utilize LangGraph checkpointer, but for now we reconstruct or pass minimal context
# For MVP: stateless + history from client? Or simple thread_id mapping if we added MemorySaver.

@router.post("/chat", response_model=ChatResponse)
async def chat_assistant(
    request: ChatRequest,
    user_email: str = Depends(get_current_user_email),
    company_id: str = Depends(get_current_company_id)
):
    """
    Chat with the AI Assistant.
    """
    try:
        # 1. Inputs
        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "company_id": company_id,
            "user_email": user_email
        }
        
        # 2. Config (Thread ID for memory)
        # Use email-based session ID if no threadId provided
        config = {
            "configurable": {"thread_id": request.threadId or f"{user_email}-session"},
            "recursion_limit": 25
        }
        
        # 3. Invoke
        # Use ainvoke or stream.
        # We need to get the LAST AI Message.
        
        # Note: Since we didn't attach MemorySaver in graph.py yet, state resets.
        # We should fix graph.py to use MemorySaver.
        
        result = await concierge_app.ainvoke(inputs, config)
        
        last_message = result["messages"][-1]
        response_text = last_message.content
        
        return ChatResponse(
            response=str(response_text),
            threadId=config["configurable"]["thread_id"]
        )
        
    except Exception as e:
        logger.error(f"Assistant Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
