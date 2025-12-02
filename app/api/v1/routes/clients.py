from fastapi import APIRouter, Depends, HTTPException
from typing import List, Union
from app.services.core.client_service import ClientService
from app.api.v1.schemas.client import Client, IndividualClient, CompanyClient

router = APIRouter()

def get_client_service():
    return ClientService()

@router.get("/{company_id}/clients", response_model=List[Client])
def get_clients(
    company_id: str, 
    service: ClientService = Depends(get_client_service)
):
    return service.get_clients(company_id)

@router.post("/{company_id}/clients", response_model=Client)
def create_client(
    company_id: str, 
    client_data: Union[IndividualClient, CompanyClient], 
    service: ClientService = Depends(get_client_service)
):
    return service.create_client(company_id, client_data)

@router.get("/{company_id}/clients/{client_id}", response_model=Client)
def get_client(
    company_id: str, 
    client_id: str, 
    service: ClientService = Depends(get_client_service)
):
    client = service.get_client(company_id, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
