from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.dependencies import (
    get_company_service, get_client_service, get_case_service,
    get_document_service, get_template_service, get_draft_service
)
from app.services.core.core_services import (
    CompanyService, ClientService, CaseService,
    DocumentService, TemplateService, DraftService
)
from app.models.domain import Company, Client, Case, Document, Template, Draft
from app.api.v1.routes import companies, clients, cases, documents, templates, drafts, users

router = APIRouter()

router.include_router(companies.router, tags=["Companies"])
router.include_router(clients.router, tags=["Clients"])
router.include_router(cases.router, tags=["Cases"])
router.include_router(documents.router, tags=["Documents"])
router.include_router(templates.router, tags=["Templates"])
router.include_router(drafts.router, tags=["Drafts"])
router.include_router(users.router, prefix="/users", tags=["Users"])


# --- Cases ---
@router.get("/{company_name}/{company_id}/clients/{client_id}/cases", response_model=List[Case])
def get_cases(company_id: str, client_id: str, service: CaseService = Depends(get_case_service)):
    return service.get_cases(company_id, client_id)

@router.post("/{company_name}/{company_id}/clients/{client_id}/cases", response_model=Case)
def create_case(company_id: str, client_id: str, case: Case, service: CaseService = Depends(get_case_service)):
    if case.companyId != company_id or case.clientId != client_id:
        raise HTTPException(status_code=400, detail="ID mismatch")
    return service.create_case(case)

@router.get("/{company_name}/{company_id}/clients/{client_id}/cases/{case_id}", response_model=Case)
def get_case(company_id: str, client_id: str, case_id: str, service: CaseService = Depends(get_case_service)):
    case = service.get_case(company_id, client_id, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

# --- Documents ---
@router.get("/{company_name}/{company_id}/documents", response_model=List[Document])
def get_documents(company_id: str, parent_id: str, service: DocumentService = Depends(get_document_service)):
    # Note: parent_id must be passed as query param or inferred
    return service.get_documents(parent_id)

@router.post("/{company_name}/{company_id}/documents", response_model=Document)
def create_document(company_id: str, document: Document, service: DocumentService = Depends(get_document_service)):
    if document.companyId != company_id:
        raise HTTPException(status_code=400, detail="Company ID mismatch")
    return service.create_document(document)

# --- Templates ---
@router.get("/{company_name}/{company_id}/templates", response_model=List[Template])
def get_templates(company_id: str, service: TemplateService = Depends(get_template_service)):
    return service.get_templates(company_id)

@router.post("/{company_name}/{company_id}/templates", response_model=Template)
def create_template(company_id: str, template: Template, service: TemplateService = Depends(get_template_service)):
    if template.companyId != company_id:
        raise HTTPException(status_code=400, detail="Company ID mismatch")
    return service.create_template(template)

# --- Drafts ---
@router.get("/{company_name}/{company_id}/cases/{case_id}/drafts", response_model=List[Draft])
def get_drafts(case_id: str, service: DraftService = Depends(get_draft_service)):
    return service.get_drafts(case_id)

@router.post("/{company_name}/{company_id}/cases/{case_id}/drafts", response_model=Draft)
def create_draft(case_id: str, draft: Draft, service: DraftService = Depends(get_draft_service)):
    if draft.caseId != case_id:
        raise HTTPException(status_code=400, detail="Case ID mismatch")
    return service.create_draft(draft)
