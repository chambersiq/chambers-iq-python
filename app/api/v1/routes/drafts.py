from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.core.draft_service import DraftService
from app.api.v1.schemas.draft import Draft, DraftCreate, DraftUpdate

router = APIRouter()

def get_draft_service():
    return DraftService()

@router.get("/{company_id}/cases/{case_id}/drafts", response_model=List[Draft])
def get_drafts(
    company_id: str, 
    case_id: str, 
    service: DraftService = Depends(get_draft_service)
):
    return service.get_drafts(company_id, case_id)

@router.get("/{company_id}/drafts", response_model=List[Draft])
def get_all_drafts(
    company_id: str, 
    service: DraftService = Depends(get_draft_service)
):
    return service.get_all_drafts(company_id)

@router.post("/{company_id}/cases/{case_id}/drafts", response_model=Draft)
def create_draft(
    company_id: str,
    case_id: str, 
    draft: DraftCreate, 
    service: DraftService = Depends(get_draft_service)
):
    if draft.caseId != case_id:
        raise HTTPException(status_code=400, detail="Case ID mismatch")
    
    # We now have company_id from URL
    # We now have company_id from URL
    return service.create_draft(company_id, draft)

@router.put("/{company_id}/drafts/{draft_id}", response_model=Draft)
def update_draft(
    company_id: str,
    draft_id: str,
    draft_update: DraftUpdate,
    service: DraftService = Depends(get_draft_service)
):
    updated_draft = service.update_draft(company_id, draft_id, draft_update)
    if not updated_draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return updated_draft

@router.get("/{company_id}/drafts/{draft_id}", response_model=Draft)
def get_draft(
    company_id: str,
    draft_id: str, 
    service: DraftService = Depends(get_draft_service)
):
    draft = service.get_draft(company_id, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft
