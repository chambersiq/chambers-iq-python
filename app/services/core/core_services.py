from typing import List, Optional
from app.repositories.core_repositories import (
    CompanyRepository, ClientRepository, CaseRepository, 
    DocumentRepository, TemplateRepository, DraftRepository
)
from app.models.domain import Company, Client, Case, Document, Template, Draft

class CompanyService:
    def __init__(self):
        self.repo = CompanyRepository()

    def create_company(self, company: Company) -> Company:
        self.repo.save(company.model_dump())
        return company

    def get_company(self, company_id: str) -> Optional[Company]:
        item = self.repo.get_by_id(company_id)
        return Company(**item) if item else None

class ClientService:
    def __init__(self):
        self.repo = ClientRepository()

    def create_client(self, client: Client) -> Client:
        self.repo.save(client.model_dump())
        return client

    def get_clients(self, company_id: str) -> List[Client]:
        items = self.repo.get_all_for_company(company_id)
        return [Client(**item) for item in items]

    def get_client(self, company_id: str, client_id: str) -> Optional[Client]:
        item = self.repo.get_by_id(company_id, client_id)
        return Client(**item) if item else None

class CaseService:
    def __init__(self):
        self.repo = CaseRepository()

    def create_case(self, case: Case) -> Case:
        # Ensure composite key structure if needed, though model handles it
        self.repo.save(case.model_dump())
        return case

    def get_cases(self, company_id: str, client_id: str) -> List[Case]:
        items = self.repo.get_all_for_client(company_id, client_id)
        return [Case(**item) for item in items]

    def get_case(self, company_id: str, client_id: str, case_id: str) -> Optional[Case]:
        item = self.repo.get_by_id(company_id, client_id, case_id)
        return Case(**item) if item else None

class DocumentService:
    def __init__(self):
        self.repo = DocumentRepository()

    def create_document(self, document: Document) -> Document:
        self.repo.save(document.model_dump())
        return document

    def get_documents(self, parent_id: str) -> List[Document]:
        items = self.repo.get_all_for_parent(parent_id)
        return [Document(**item) for item in items]

class TemplateService:
    def __init__(self):
        self.repo = TemplateRepository()

    def create_template(self, template: Template) -> Template:
        # Construct sort key
        data = template.model_dump()
        data["caseType#templateId"] = f"{template.caseType}#{template.templateId}"
        self.repo.save(data)
        return template

    def get_templates(self, company_id: str) -> List[Template]:
        items = self.repo.get_all_for_company(company_id)
        return [Template(**item) for item in items]

class DraftService:
    def __init__(self):
        self.repo = DraftRepository()

    def create_draft(self, draft: Draft) -> Draft:
        self.repo.save(draft.model_dump())
        return draft

    def get_drafts(self, case_id: str) -> List[Draft]:
        items = self.repo.get_all_for_case(case_id)
        return [Draft(**item) for item in items]
