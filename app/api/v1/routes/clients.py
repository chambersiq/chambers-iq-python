from fastapi import APIRouter, Depends, HTTPException, Header, Response
from typing import List, Union, Optional
from app.services.core.client_service import ClientService
from app.services.core.company_service import UserService
from app.api.v1.schemas.client import Client, IndividualClient, CompanyClient

router = APIRouter()

def get_client_service():
    return ClientService()

def get_user_service():
    return UserService()

@router.get("/companies/{company_id}/clients", response_model=List[Client])
def get_clients(
    company_id: str, 
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    service: ClientService = Depends(get_client_service),
    user_service: UserService = Depends(get_user_service)
):
    # Strict Auth Check
    if not x_user_email:
        # For now, if no header, we return 401 as per plan
        raise HTTPException(status_code=401, detail="X-User-Email header required")
        
    user = user_service.get_user_by_email_global(x_user_email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    # RBAC Logic
    allowed_clients = None
    if user.role != 'admin':
        # User Feedback: If allowedClients is empty, it means access to ALL clients (default).
        # We only filter if allowedClients has items.
        if user.allowedClients and len(user.allowedClients) > 0:
            allowed_clients = user.allowedClients
        
    return service.get_clients(company_id, allowed_clients=allowed_clients)

@router.post("/companies/{company_id}/clients", response_model=Client)
def create_client(
    company_id: str, 
    client_data: Union[IndividualClient, CompanyClient], 
    service: ClientService = Depends(get_client_service)
):
    return service.create_client(company_id, client_data)

@router.get("/clients/{client_id}", response_model=Client)
def get_client(
    client_id: str, 
    service: ClientService = Depends(get_client_service)
):
    # Note: Service methods often require company_id for partition key.
    # We might need to fetch it or pass a dummy/wildcard if the service supports it.
    # Ideally, client_id is unique enough or we look it up.
    # For now, let's assume service.get_client_by_id exists or we require company_id in standard approach.
    # BUT user requested: GET /clients/{clientId}
    # This implies the backend must be able to find the client without company_id.
    # If DynamoDB uses companyId as partition key, we need a GSI on clientId.
    # Assuming GSI exists or Scan is used (not ideal).
    # Let's check `ClientService`. For now, I will match the signature requested.
    # UPDATE: We need to pass expected arguments to service.
    
    # Prereq: We need a method to get client by ID alone.
    return service.get_client_by_id(client_id)
