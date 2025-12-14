from typing import List, Optional
import uuid
from datetime import datetime
from app.repositories.draft_repository import DraftRepository
from app.repositories.case_repository import CaseRepository
from app.repositories.client_repository import ClientRepository
from app.repositories.template_repository import TemplateRepository
from app.agents.template_generator import TemplateGeneratorAgent
from app.api.v1.schemas.draft import Draft, DraftCreate, DraftUpdate

class DraftService:
    def __init__(self):
        self.repo = DraftRepository()
        self.case_repo = CaseRepository()
        self.client_repo = ClientRepository()
        self.template_repo = TemplateRepository()
        self.template_generator = TemplateGeneratorAgent()

    def _enrich_draft_context(self, draft: Draft) -> Draft:
        # Fetch Case Name
        if draft.caseId:
             # CaseRepo.get_by_id_scan or global? Draft has companyId.
             # Ideally get_by_id(company, client?, case) but we often don't have clientId handy here easily unless we look it up.
             # But Draft HAS clientId.
             case = self.case_repo.get_by_id(draft.companyId, draft.clientId, draft.caseId)
             if case:
                 draft.caseName = case.get('caseName') or case.get('caseNumber')
        
        # Fetch Client Name
        if draft.clientId:
            client = self.client_repo.get_by_id(draft.companyId, draft.clientId)
            if client:
                data = client.get('data', {})
                c_type = data.get('clientType')
                if c_type == 'individual':
                    draft.clientName = data.get('fullName')
                elif c_type == 'company':
                    draft.clientName = data.get('companyName')

        # Fetch Template Name & Document Type (if not set)
        if draft.templateId:
            template = self.template_repo.get_by_id_global(draft.templateId)
            if template:
                draft.templateName = template.get('name')
                # If documentType is generic, try to infer from template category
                if draft.documentType == "General" and template.get('category'):
                    draft.documentType = template.get('category')
        
        return draft

    def create_draft(self, company_id: str, data: DraftCreate) -> Draft:
        draft_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        draft_dict = data.model_dump()
        draft_dict.update({
            "companyId": company_id,
            "draftId": draft_id,
            "lastEditedAt": now,
            "createdAt": now
        })
        
        self.repo.create(draft_dict)
        return self._enrich_draft_context(Draft(**draft_dict))

    def update_draft(self, company_id: str, draft_id: str, data: 'DraftUpdate') -> Optional[Draft]:
        # Need caseId for PK
        current_draft = self.get_draft(company_id, draft_id)
        if not current_draft:
            return None
            
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return current_draft
            
        updates["lastEditedAt"] = datetime.utcnow().isoformat()
        
        self.repo.update(current_draft.caseId, draft_id, updates)
        return self.get_draft(company_id, draft_id)

    def get_drafts(self, company_id: str, case_id: str) -> List[Draft]:
        items = self.repo.get_all_for_case(company_id, case_id)
        return [self._enrich_draft_context(Draft(**item)) for item in items]

    def get_all_drafts(self, company_id: str) -> List[Draft]:
        items = self.repo.get_all_for_company(company_id)
        return [self._enrich_draft_context(Draft(**item)) for item in items]

    def get_draft(self, company_id: str, draft_id: str) -> Optional[Draft]:
        item = self.repo.get_by_id_global(draft_id)
        if item:
            return self._enrich_draft_context(Draft(**item))
        return None

    def delete_draft(self, company_id: str, draft_id: str) -> bool:
        """
        Delete a draft by ID.
        """
        draft = self.get_draft(company_id, draft_id)
        if not draft:
            return False
            
        # Verify company ownership
        if draft.companyId != company_id:
            return False # Or raise PermissionError
            
        # Delete using caseId (PK) and draftId (SK)
        self.repo.delete(draft.caseId, draft.draftId)
        return True

    async def generate_ai_template_content(self, case_id: str, document_type: str) -> str:
        """Generate template content using AI based on case data"""

        # Get complete case data
        case = self.case_repo.get_by_id_global(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        client = self.client_repo.get_by_id(case.get('companyId'), case.get('clientId'))
        if not client:
            raise ValueError(f"Client for case {case_id} not found")

        # Extract additional facts if available (placeholder for now)
        case_facts = {"summary": "Case facts to be extracted from documents"}

        # Prepare comprehensive case data for AI
        case_data = {
            'case': case,
            'client': client,
            'case_facts': case_facts
        }

        # Remove sensitive fields
        sensitive_fields = ['id', 'created_at', 'updated_at', 'internal_notes']
        for obj in [case_data['case'], case_data['client']]:
            for field in sensitive_fields:
                obj.pop(field, None)

        # Generate template using AI agent
        return await self.template_generator.generate_template(case_data, document_type)
