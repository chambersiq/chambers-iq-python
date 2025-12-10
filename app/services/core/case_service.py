from typing import List, Optional
import uuid
from datetime import datetime
from app.repositories.case_repository import CaseRepository
from app.repositories.client_repository import ClientRepository
from app.api.v1.schemas.case import Case, CaseCreate

class CaseService:
    def __init__(self):
        self.repo = CaseRepository()
        self.client_repo = ClientRepository()

    def create_case(self, company_id: str, client_id: str, data: CaseCreate) -> Case:
        case_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        case_dict = data.model_dump()
        
        # Auto-generate case number if not provided
        if not case_dict.get("caseNumber"):
            # Simple auto-generation: CASE-{YYYY}-{UUID_PREFIX}
            # In a real app, this would likely be a counter in DB
            year = datetime.utcnow().year
            short_id = case_id[:8].upper()
            case_dict["caseNumber"] = f"CASE-{year}-{short_id}"

        # Fetch client details to denormalize clientName
        client = self.client_repo.get_by_id(company_id, client_id)
        client_name = "Unknown Client"
        if client:
            client_data = client.get("data", {})
            c_type = client_data.get("clientType")
            if c_type == "individual":
                client_name = client_data.get("fullName", "")
            elif c_type == "company":
                client_name = client_data.get("companyName", "")

        case_dict.update({
            "companyId#clientId": f"{company_id}#{client_id}", # PK
            "companyId": company_id,
            "clientId": client_id,
            "clientName": client_name, # Denormalized
            "caseId": case_id, # SK
            "createdAt": now,
            "updatedAt": now
        })
        
        self.repo.create(case_dict)
        return Case(**case_dict)

    def _populate_client_name(self, case_obj: Case) -> Case:
        if not case_obj.clientName or case_obj.clientName == "Unknown Client":
            # Try to fetch client name
            client = self.client_repo.get_by_id_global(case_obj.clientId)
            if client:
                # ClientRepo returns raw item. Need to check data dict.
                c_data = client.get('data', {})
                c_type = c_data.get('clientType')
                name = "Unknown"
                if c_type == 'individual':
                    name = f"{c_data.get('fullName', '')}".strip() # Schema uses fullName
                elif c_type == 'company':
                    name = c_data.get('companyName', '')
                
                # If name found, update object (and maybe DB? For now just object)
                if name:
                    case_obj.clientName = name
        return case_obj

    def get_cases(self, company_id: str, client_id: str) -> List[Case]:
        items = self.repo.get_all_for_client(company_id, client_id)
        return [self._populate_client_name(Case(**item)) for item in items]

    def get_all_cases(self, company_id: str) -> List[Case]:
        items = self.repo.get_all_for_company(company_id)
        return [self._populate_client_name(Case(**item)) for item in items]

    def get_case(self, company_id: str, client_id: str, case_id: str) -> Optional[Case]:
        item = self.repo.get_by_id(company_id, client_id, case_id)
        return self._populate_client_name(Case(**item)) if item else None

    def update_case(self, company_id: str, client_id: str, case_id: str, data: CaseCreate) -> Case:
        updates = data.model_dump(exclude_unset=True)
        updates["updatedAt"] = datetime.utcnow().isoformat()
        
        attributes = self.repo.update(company_id, client_id, case_id, updates)
        return self._populate_client_name(Case(**attributes))

    def get_case_by_id(self, company_id: str, case_id: str) -> Optional[Case]:
        item = self.repo.get_by_id_scan(company_id, case_id)
        return self._populate_client_name(Case(**item)) if item else None

    def delete_case(self, company_id: str, client_id: str, case_id: str) -> None:
        self.repo.delete(company_id, client_id, case_id)

    def get_case_by_id_only(self, case_id: str) -> Optional[Case]:
        item = self.repo.get_by_id_global(case_id)
        return self._populate_client_name(Case(**item)) if item else None

    def get_cases_by_client(self, client_id: str) -> List[Case]:
        items = self.repo.get_all_by_client_global(client_id)
        return [self._populate_client_name(Case(**item)) for item in items]

    def create_case_for_client(self, client_id: str, data: CaseCreate) -> Case:
        # We need company_id to create a case (part of PK).
        # We must look up the client first to find their company_id.
        client = self.client_repo.get_by_id_global(client_id)
        if not client:
             raise ValueError("Client not found")
        
        company_id = client["companyId"]
        return self.create_case(company_id, client_id, data)

    def update_case_by_id(self, case_id: str, data: CaseCreate) -> Case:
        # We need keys to update.
        case = self.get_case_by_id_only(case_id)
        if not case:
            raise ValueError("Case not found")
        return self.update_case(case.companyId, case.clientId, case_id, data)

    def delete_case_by_id(self, case_id: str) -> None:
        case = self.get_case_by_id_only(case_id)
        if case:
            self.delete_case(case.companyId, case.clientId, case_id)
