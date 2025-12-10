from typing import List, Optional, Union
import uuid
from datetime import datetime
from app.repositories.client_repository import ClientRepository
from app.repositories.case_repository import CaseRepository
from app.api.v1.schemas.client import Client, ClientCreate, IndividualClient, CompanyClient

class ClientService:
    def __init__(self):
        self.repo = ClientRepository()
        self.case_repo = CaseRepository()

    def create_client(self, company_id: str, data: Union[IndividualClient, CompanyClient]) -> dict:
        client_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # We store it nested for DynamoDB structure (cleaner)
        client_dict = {
            "companyId": company_id,
            "clientId": client_id,
            "data": data.model_dump(), 
            "createdAt": now,
            "updatedAt": now,
            "totalCases": 0,
            "name": data.fullName if isinstance(data, IndividualClient) else data.companyName,
            "email": data.email if isinstance(data, IndividualClient) else data.contactEmail,
            "status": data.status
        }
        
        self.repo.create(client_dict)
        
        # But return it flattened for the API response
        flat_data = data.model_dump()
        response_dict = {**client_dict, **flat_data}
        # Remove the 'data' key from response
        response_dict.pop('data', None)
        
        return response_dict

    def get_clients(self, company_id: str, allowed_clients: Optional[List[str]] = None) -> List[dict]:
        items = self.repo.get_all_for_company(company_id)
        
        # Efficiently calculate active case counts
        # Fetch all active cases for the company
        active_cases = self.case_repo.get_all_for_company(company_id, include_archived=False)
        case_counts = {}
        for case in active_cases:
            # Filter out closed cases if "Active" means status != closed? 
            # User said "Active" cases. Usually "Active" status. 
            # But maybe they mean "Not Archived"? 
            # "Total cases (should show only Active) count is zero."
            # The prompt implies status='active'. 
            # Let's count cases that are NOT archived (soft deleted) AND status != 'closed'?
            # For now, let's stick to "Not Archived" as the base, and maybe filter by status if needed.
            # Interpreting "Active" as non-archived for now, or maybe status='active'.
            # Let's count cases where status is NOT 'closed' and NOT archived.
            if case.get('status') != 'closed': # active, discovery, trial, etc.
                c_id = case.get('clientId')
                if c_id:
                    case_counts[c_id] = case_counts.get(c_id, 0) + 1

        clients = []
        for item in items:
            # Flatten the 'data' dictionary into the top-level dictionary
            data = item.pop('data', {})
            client_dict = {**item, **data}
            
            # Filter if restricted
            if allowed_clients is not None:
                # If allowed_clients is empty list, they see NOTHING (except maybe they shouldn't exist)
                # We check if clientId is in the allowed list
                if client_dict.get('clientId') not in allowed_clients:
                    continue
            
            # Populate totalCases
            client_dict['totalCases'] = case_counts.get(client_dict['clientId'], 0)
            
            clients.append(client_dict)
        return clients

    def get_client(self, company_id: str, client_id: str) -> Optional[dict]:
        item = self.repo.get_by_id(company_id, client_id)
        if item:
            data = item.pop('data', {})
            client_dict = {**item, **data}
            
            # Calculate active cases
            # Use get_all_for_company just like the list view to guarantee consistency
            cases = self.case_repo.get_all_for_company(company_id, client_id, include_archived=False) 
            # Note: get_all_for_company only takes 2 args: company_id, include_archived. 
            # I made a mistake in previous thought, client_id is not passed to get_all_for_company.
            # wait, I need to check the signature of get_all_for_company
            # It is: def get_all_for_company(self, company_id: str, include_archived: bool = False)
            
            cases = self.case_repo.get_all_for_company(company_id, include_archived=False)
            
            # Filter active (not closed, not archived) and for specific client
            active_count = sum(1 for c in cases if c.get('clientId') == client_id and c.get('status') != 'closed')
            
            client_dict['totalCases'] = active_count
            
            return client_dict
        return None

    def get_client_by_id(self, client_id: str) -> Optional[dict]:
        item = self.repo.get_by_id_global(client_id)
        if item:
            data = item.pop('data', {})
            client_dict = {**item, **data}
            
            # Calculate active cases
            company_id = client_dict.get('companyId')
            if company_id:
                # Use get_all_for_company just like the list view to guarantee consistency
                cases = self.case_repo.get_all_for_company(company_id, include_archived=False)
                active_count = sum(1 for c in cases if c.get('clientId') == client_id and c.get('status') != 'closed')
                client_dict['totalCases'] = active_count
            else:
                 client_dict['totalCases'] = 0

            return client_dict
        return None
