from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.core.case_service import CaseService
from app.api.v1.schemas.case import Case, CaseCreate

router = APIRouter()

def get_case_service():
    return CaseService()

@router.get("/clients/{client_id}/cases", response_model=List[Case])
def get_cases(
    client_id: str, 
    service: CaseService = Depends(get_case_service)
):
    return service.get_cases_by_client(client_id)

@router.get("/companies/{company_id}/cases", response_model=List[Case])
def get_all_cases(
    company_id: str, 
    service: CaseService = Depends(get_case_service)
):
    return service.get_all_cases(company_id)

@router.post("/clients/{client_id}/cases", response_model=Case)
def create_case(
    client_id: str, 
    case: CaseCreate, 
    service: CaseService = Depends(get_case_service)
):
    # Service needs company_id usually. We might need to look up client first to get company_id.
    return service.create_case_for_client(client_id, case)

@router.get("/cases/{case_id}", response_model=Case)
def get_case(
    case_id: str, 
    service: CaseService = Depends(get_case_service)
):
    case = service.get_case_by_id_only(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.put("/cases/{case_id}", response_model=Case)
def update_case(
    case_id: str, 
    case: CaseCreate, 
    service: CaseService = Depends(get_case_service)
):
    return service.update_case_by_id(case_id, case)

@router.delete("/cases/{case_id}")
def delete_case(
    case_id: str, 
    service: CaseService = Depends(get_case_service)
):
    service.delete_case_by_id(case_id)
    return {"message": "Case deleted successfully"}
