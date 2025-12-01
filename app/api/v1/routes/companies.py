from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.core.company_service import CompanyService, UserService
from app.api.v1.schemas.company import Company, CompanyCreate, User, UserCreate

router = APIRouter()

def get_company_service():
    return CompanyService()

def get_user_service():
    return UserService()

# --- Companies ---
@router.post("/companies", response_model=Company)
def create_company(
    company: CompanyCreate, 
    service: CompanyService = Depends(get_company_service)
):
    try:
        return service.create_company(company)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/companies/{company_id}", response_model=Company)
def get_company(
    company_id: str, 
    service: CompanyService = Depends(get_company_service)
):
    company = service.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

# --- Users ---
@router.post("/{company_name}/{company_id}/users", response_model=User)
def create_user(
    company_id: str, 
    user: UserCreate, 
    service: UserService = Depends(get_user_service)
):
    try:
        return service.create_user(company_id, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{company_name}/{company_id}/users", response_model=List[User])
def get_users(
    company_id: str, 
    service: UserService = Depends(get_user_service)
):
    return service.get_users(company_id)
