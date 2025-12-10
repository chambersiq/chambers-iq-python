from typing import List, Optional, Union
import uuid
from datetime import datetime
from app.repositories.client_repository import ClientRepository
from app.api.v1.schemas.client import Client, ClientCreate, IndividualClient, CompanyClient

class ClientService:
    def __init__(self):
        self.repo = ClientRepository()

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
            
            clients.append(client_dict)
        return clients

    def get_client(self, company_id: str, client_id: str) -> Optional[dict]:
        item = self.repo.get_by_id(company_id, client_id)
        if item:
            data = item.pop('data', {})
            client_dict = {**item, **data}
            return client_dict
        return None

    def get_client_by_id(self, client_id: str) -> Optional[dict]:
        item = self.repo.get_by_id_global(client_id)
        if item:
            data = item.pop('data', {})
            client_dict = {**item, **data}
            return client_dict
        return None
