from typing import List, Optional
import uuid
from datetime import datetime
from app.repositories.draft_repository import DraftRepository
from app.api.v1.schemas.draft import Draft, DraftCreate, DraftUpdate

class DraftService:
    def __init__(self):
        self.repo = DraftRepository()

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
        self.repo.create(draft_dict)
        return Draft(**draft_dict)

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
        return [Draft(**item) for item in items]

    def get_all_drafts(self, company_id: str) -> List[Draft]:
        items = self.repo.get_all_for_company(company_id)
        return [Draft(**item) for item in items]

    def get_draft(self, company_id: str, draft_id: str) -> Optional[Draft]:
        item = self.repo.get_by_id_global(draft_id)
        return Draft(**item) if item else None
