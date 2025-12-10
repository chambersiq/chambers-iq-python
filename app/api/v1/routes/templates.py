from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.services.core.template_service import TemplateService
from app.api.v1.schemas.template import Template, TemplateCreate

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
