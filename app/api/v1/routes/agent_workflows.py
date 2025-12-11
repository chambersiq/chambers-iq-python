from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.agents.workflows.drafting.graph import app as agent_app
from app.agents.workflows.drafting.schema import AgentNode
from app.core.config import settings
import uuid
import asyncio

router = APIRouter()

from app.services.core.case_service import CaseService

# --- Schemas ---

class WorkflowStartRequest(BaseModel):
    case_id: str
    company_id: Optional[str] = None # Optional, inferred if missing
    case_type: str
    client_id: str
    template_id: Optional[str] = None
    initial_instructions: Optional[str] = None

class WorkflowResponse(BaseModel):
    thread_id: str
    status: str # "running", "interrupted", "completed"
    current_node: str
    next_node: Optional[str]
    current_state: Dict[str, Any]

class WorkflowResumeRequest(BaseModel):
    human_verdict: str # "approve", "reject", "refine"
    human_feedback: Optional[str] = None

# --- Endpoints ---

@router.post("/start", response_model=WorkflowResponse)
async def start_workflow(request: WorkflowStartRequest, background_tasks: BackgroundTasks):
    """
    Start a new Multi-Agent Drafting Workflow.
    """
    # 1. Resolve Company ID if missing
    company_id = request.company_id
    if not company_id:
        # Try to look up case globally
        # Note: This uses a scan or GSI, slightly slower but necessary if frontend doesn't send context
        case_service = CaseService()
        case = case_service.get_case_by_id_only(request.case_id)
        if case:
            company_id = case.companyId
        else:
            raise HTTPException(status_code=404, detail="Case not found, cannot infer company_id")
            
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "company_id": company_id,
        "case_id": request.case_id,
        "case_type": request.case_type,
        "client_id": request.client_id,
        "template_id": request.template_id,
        "created_at": "2023-01-01", # TODO: Use real date
        "current_section_idx": 0,
        "completed_section_ids": [],
        "iteration_count": 0
    }
    
    # Run the graph until the first interrupt asynchronously
    # Note: For production, use a task queue like Celery/Arq
    # Here we use BackgroundTasks but we need a wrapper to run async gen
    # actually, iterating an async generator in background task is tricky in FastAPI.
    # We will run just the first step synchronously or rely on 'stream' endpoint.
    # For simplicity, let's run it until interrupt immediately (await logic).
    
    # We initiate the state update
    await agent_app.aupdate_state(config, initial_state)
    
    # Kick off execution
    # We use a helper function to run until interrupt
    background_tasks.add_task(run_agent_until_interrupt, config)
    
    return WorkflowResponse(
        thread_id=thread_id,
        status="started",
        current_node="start",
        next_node=AgentNode.PLANNER,
        current_state=initial_state
    )

@router.get("/{thread_id}/status", response_model=WorkflowResponse)
async def get_workflow_status(thread_id: str):
    """
    Get the current status of a workflow thread.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        current_state_snapshot = await agent_app.aget_state(config)
    except Exception:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    if not current_state_snapshot: # e.g. tuple might be empty
         raise HTTPException(status_code=404, detail="Thread state empty")

    values = current_state_snapshot.values
    next_node = current_state_snapshot.next
    
    # Format next_node for UI (it comes as a tuple from LangGraph)
    next_node_str = ""
    if next_node:
        if isinstance(next_node, (list, tuple)):
            # Try to get value if Enum, else str
            parts = []
            for n in next_node:
                if hasattr(n, "value"):
                    parts.append(str(n.value))
                else:
                    parts.append(str(n))
            next_node_str = ", ".join(parts)
        else:
            next_node_str = str(next_node.value) if hasattr(next_node, "value") else str(next_node)
            
    print(f"DEBUG Status Check: next_node={next_node_str}")
    print(f"DEBUG Status Check: error_in_values={values.get('error')}")
    
    status = "running"
    if values.get("error"):
        status = "failed"
    elif not next_node:
        status = "completed"
    elif "human_review" in next_node_str or "AgentNode.HUMAN" in next_node_str:
        status = "interrupted_for_human"
    
    return WorkflowResponse(
        thread_id=thread_id,
        status=status,
        current_node=next_node_str, # Use cleaned string
        next_node=next_node_str,
        current_state=values
    )

@router.post("/{thread_id}/resume", response_model=WorkflowResponse)
async def resume_workflow(thread_id: str, request: WorkflowResumeRequest, background_tasks: BackgroundTasks):
    """
    Resume an interrupted workflow with human feedback.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Update state with human input
    update_dict = {
        "human_verdict": request.human_verdict,
        "human_feedback": request.human_feedback
    }
    
    await agent_app.aupdate_state(config, update_dict)
    
    # Continue execution
    background_tasks.add_task(run_agent_until_interrupt, config)
    
    return await get_workflow_status(thread_id)


async def run_agent_until_interrupt(config):
    """
    Helper to drain the generator.
    """
    try:
        # We pass context as None because state is already saved
        async for event in agent_app.astream(None, config=config):
            pass # Just let it run until it stops or interrupts
    except Exception as e:
        error_msg = str(e)
        print(f"Error in background agent run: {error_msg}")
        
        # Friendly error for recursion limit
        if "recursion limit" in error_msg.lower():
            error_msg = "Workflow safety limit reached. Please confirm 'Refine' or 'Force Approval' to continue."

        # Save error to state so UI knows
        try:
             print(f"DEBUG: Attempting to save error to state: {error_msg}")
             await agent_app.aupdate_state(config, {"error": error_msg})
             print("DEBUG: Saved error to state.")
        except Exception as update_err:
             print(f"DEBUG: Failed to save error state: {update_err}")
             pass
