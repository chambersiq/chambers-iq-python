from app.services.core.core_services import (
    CompanyService, ClientService, CaseService, 
    DocumentService, TemplateService, DraftService
)

def get_company_service() -> CompanyService:
    return CompanyService()

def get_client_service() -> ClientService:
    return ClientService()

def get_case_service() -> CaseService:
    return CaseService()

def get_document_service() -> DocumentService:
    return DocumentService()

def get_template_service() -> TemplateService:
    return TemplateService()

def get_draft_service() -> DraftService:
    return DraftService()
