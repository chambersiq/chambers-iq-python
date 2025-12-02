from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.core.case_service import CaseService
from app.api.v1.schemas.case import Case, CaseCreate

router = APIRouter()

def get_case_service():
    return CaseService()

@router.get("/{company_id}/clients/{client_id}/cases", response_model=List[Case])
def get_cases(
    company_id: str, 
    client_id: str, 
    service: CaseService = Depends(get_case_service)
):
    return service.get_cases(company_id, client_id)

@router.get("/{company_id}/cases", response_model=List[Case])
def get_all_cases(
    company_id: str, 
    service: CaseService = Depends(get_case_service)
):
    return service.get_all_cases(company_id)

@router.post("/{company_id}/clients/{client_id}/cases", response_model=Case)
def create_case(
    company_id: str, 
    client_id: str, 
    case: CaseCreate, 
    service: CaseService = Depends(get_case_service)
):
    return service.create_case(company_id, client_id, case)

@router.get("/{company_id}/clients/{client_id}/cases/{case_id}", response_model=Case)
def get_case(
    company_id: str, 
    client_id: str, 
    case_id: str, 
    service: CaseService = Depends(get_case_service)
):
    case = service.get_case(company_id, client_id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.put("/{company_id}/clients/{client_id}/cases/{case_id}", response_model=Case)
def update_case(
    company_id: str, 
    client_id: str, 
    case_id: str, 
    case: CaseCreate, 
    service: CaseService = Depends(get_case_service)
):
    return service.update_case(company_id, client_id, case_id, case)

@router.delete("/{company_id}/clients/{client_id}/cases/{case_id}")
def delete_case(
    company_id: str, 
    client_id: str, 
    case_id: str, 
    service: CaseService = Depends(get_case_service)
):
    service.delete_case(company_id, client_id, case_id)
    return {"message": "Case deleted successfully"}

@router.get("/{company_id}/cases/{case_id}", response_model=Case)
def get_case_by_id(
    company_id: str, 
    case_id: str, 
    service: CaseService = Depends(get_case_service)
):
    case = service.get_case_by_id(company_id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case
