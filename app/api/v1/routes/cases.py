from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.core.case_service import CaseService
from app.api.v1.schemas.case import Case, CaseCreate

router = APIRouter()

def get_case_service():
    return CaseService()

from app.api.v1.dependencies import verify_company_access
from fastapi import Header

@router.get("/clients/{client_id}/cases", response_model=List[Case])
def get_cases(
    client_id: str, 
    x_company_id: str = Header(..., alias="X-Company-Id"),
    service: CaseService = Depends(get_case_service)
):
    # Pass company_id to service to ensure data isolation
    return service.get_cases_by_client(x_company_id, client_id)

@router.get("/companies/{company_id}/cases", response_model=List[Case], dependencies=[Depends(verify_company_access)])
def get_all_cases(
    company_id: str, 
    service: CaseService = Depends(get_case_service)
):
    return service.get_all_cases(company_id)

@router.post("/clients/{client_id}/cases", response_model=Case)
def create_case(
    client_id: str, 
    case: CaseCreate, 
    x_company_id: str = Header(..., alias="X-Company-Id"),
    service: CaseService = Depends(get_case_service)
):
    # Ensure creation is scoped to the header company
    return service.create_case_for_client(x_company_id, client_id, case)

@router.get("/cases/{case_id}", response_model=Case)
def get_case(
    case_id: str, 
    x_company_id: str = Header(..., alias="X-Company-Id"),
    service: CaseService = Depends(get_case_service)
):
    case = service.get_case_by_id(x_company_id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.put("/cases/{case_id}", response_model=Case)
def update_case(
    case_id: str, 
    case: CaseCreate, 
    x_company_id: str = Header(..., alias="X-Company-Id"),
    service: CaseService = Depends(get_case_service)
):
    return service.update_case_by_id(x_company_id, case_id, case)

@router.delete("/cases/{case_id}")
def delete_case(
    case_id: str, 
    x_company_id: str = Header(..., alias="X-Company-Id"),
    service: CaseService = Depends(get_case_service)
):
    service.delete_case_by_id(x_company_id, case_id)
    return {"message": "Case deleted successfully"}
