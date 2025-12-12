from typing import List, Optional, Union
from langchain_core.tools import tool
from app.services.core.client_service import ClientService
from app.services.core.case_service import CaseService
from app.api.v1.schemas.client import ClientCreate, IndividualClient, CompanyClient
from app.api.v1.schemas.case import CaseCreate

# Initialize services
client_service = ClientService()
case_service = CaseService()

@tool
def search_clients(company_id: str, query: str = ""):
    """
    Search for clients in the system.
    Args:
        company_id: The ID of the law firm/company.
        query: Optional name or email to filter by. If empty, lists recent clients.
    """
    # Get all clients
    clients = client_service.get_clients(company_id)
    
    if not query:
        return clients[:5] # Return top 5 if no query
        
    query = query.lower()
    filtered = []
    
    for c in clients:
        name = c.get('name', '').lower()
        email = c.get('email', '').lower()
        if query in name or query in email:
            filtered.append(c)
            
    return filtered[:5]

@tool
def get_client_details(company_id: str, client_id: str):
    """
    Get detailed information about a specific client, including case count.
    """
    return client_service.get_client(company_id, client_id)

@tool
def search_cases(company_id: str, query: str = "", client_id: Optional[str] = None):
    """
    Search for cases in the system.
    Args:
        company_id: Law firm ID.
        query: Case name or number to search for.
        client_id: Optional, filter by specific client.
    """
    if client_id:
        cases = case_service.get_cases(company_id, client_id)
    else:
        cases = case_service.get_all_cases(company_id)
        
    if not query:
        return cases[:5]
        
    query = query.lower()
    filtered = []
    for c in cases:
        # c is a Case object (Pydantic model)
        name = (c.caseName or "").lower()
        number = (c.caseNumber or "").lower()
        if query in name or query in number:
            filtered.append(c.model_dump())
            
    return filtered[:5]

@tool
def create_new_client(company_id: str, client_data: dict):
    """
    Create a new client in the system.
    Args:
        company_id: Law firm ID.
        client_data: Dictionary containing client details matching the Client schema. 
                     Must include 'clientType': 'individual' or 'company'.
    """
    # 1. Validate / Construct the proper Pydantic model
    # The client_service expects a ClientCreate (RootModel) which wraps Individual/Company
    
    # Ensure clientType is present
    if "clientType" not in client_data:
        # Fallback or try to infer, but better to enforce agent to provide it
        # based on prompt instructions.
        client_data["clientType"] = "individual" # Default?
        
    try:
        if client_data["clientType"] == "individual":
            model = IndividualClient(**client_data)
        else:
            model = CompanyClient(**client_data)
            
        # Service takes IndividualClient or CompanyClient directly
        return client_service.create_client(company_id, model)
        
    except Exception as e:
        return f"Error validation client data: {str(e)}"

@tool
def create_new_case(company_id: str, client_id: str, case_data: dict):
    """
    Create a new case for a client.
    Args:
        company_id: Law firm ID.
        client_id: The ID of the client.
        case_data: Dictionary containing case details matching the Case schema.
    """
    try:
        # Validate using CaseCreate schema
        # Inject defaults if missing
        if "caseSummary" not in case_data:
             case_data["caseSummary"] = "Created via AI Assistant"
             
        if "status" not in case_data:
             case_data["status"] = "active"
             
        model = CaseCreate(**case_data)
        return case_service.create_case(company_id, client_id, model)
    except Exception as e:
        return f"Error creating case: {str(e)}"

concierge_tools = [search_clients, get_client_details, search_cases, create_new_client, create_new_case]
