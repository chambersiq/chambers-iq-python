from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import List
from app.services.core.template_service import TemplateService
from app.api.v1.schemas.template import Template, TemplateCreate, TemplateGenerationRequest

router = APIRouter()

def get_template_service():
    return TemplateService()

@router.get("/companies/{company_id}/templates", response_model=List[Template])
def get_templates(
    company_id: str, 
    service: TemplateService = Depends(get_template_service)
):
    return service.get_templates(company_id)

@router.post("/companies/{company_id}/templates", response_model=Template)
def create_template(
    company_id: str, 
    template: TemplateCreate, 
    service: TemplateService = Depends(get_template_service)
):
    return service.create_template(company_id, template)

@router.get("/templates/{template_id}", response_model=Template)
def get_template(
    template_id: str, 
    service: TemplateService = Depends(get_template_service)
):
    # Pass ignored company_id as service method now uses global lookup
    template = service.get_template("ignored", template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.post("/companies/{company_id}/templates/ai/upload")
async def upload_sample_document(
    company_id: str,
    generation_id: str,
    file: UploadFile = File(...),
    service: TemplateService = Depends(get_template_service)
):
    content = await file.read()
    s3_key = service.upload_sample_document(
        company_id, 
        generation_id, 
        file.filename, 
        content, 
        file.content_type
    )
    return {"status": "success", "s3Key": s3_key}

@router.post("/companies/{company_id}/templates/ai/generate")
def generate_template(
    company_id: str,
    request: TemplateGenerationRequest,
    service: TemplateService = Depends(get_template_service)
):
    content = service.generate_template_from_samples(company_id, request.generationId, request.prompt)
    return {"content": content}

from app.agents.workflows.templates.template_architect import agent_app
from app.api.v1.schemas.template import WorkflowStartRequest, WorkflowReviewRequest
import uuid

@router.post("/ai/workflow/start")
def start_workflow(
    request: WorkflowStartRequest,
    service: TemplateService = Depends(get_template_service)
):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "sample_docs": request.sampleDocs,
        "template_approved": False,
        "status": "analyzing_samples",
        "current_step": "template_architect",
        "is_simulation": request.is_simulation or False
    }
    
    # Start the workflow
    # Use invoke mostly, but stream could be better for long running. 
    # For now we invoke to get to the first checkpoint.
    result = agent_app.invoke(initial_state, config)
    
    return {
        "threadId": thread_id,
        "status": result.get("status"),
        "currentStep": result.get("current_step"),
        "template": result.get("template")
    }

@router.get("/ai/workflow/{thread_id}")
def get_workflow_status(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state = agent_app.get_state(config)
    
    if not state.values:
         raise HTTPException(status_code=404, detail="Workflow not found")
         
    return {
        "threadId": thread_id,
        "status": state.values.get("status"),
        "currentStep": state.values.get("current_step"),
        "template": state.values.get("template"),
        "template": state.values.get("template"),
        "attorneyFeedback": state.values.get("attorney_feedback"),
        "revisionSummary": state.values.get("revision_summary")
    }

@router.post("/ai/workflow/{thread_id}/review")
def review_workflow(
    thread_id: str,
    review: WorkflowReviewRequest
):
    config = {"configurable": {"thread_id": thread_id}}
    
    # Update state with approval
    agent_app.update_state(config, {
        "template_approved": review.approved,
        "attorney_feedback": review.feedback
    })
    
    # Resume workflow
    # We pass None as input because we just updated state
    result = agent_app.invoke(None, config)
    
    return {
        "threadId": thread_id,
        "status": result.get("status"),
        "currentStep": result.get("current_step"),
        "finalDocument": result.get("final_document")
    }
