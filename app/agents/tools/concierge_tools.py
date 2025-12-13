import json
import os
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
from langchain_core.tools import tool
from app.services.core.client_service import ClientService
from app.services.core.case_service import CaseService
from app.api.v1.schemas.client import ClientCreate, IndividualClient, CompanyClient
from app.api.v1.schemas.case import CaseCreate

# Initialize services
client_service = ClientService()
case_service = CaseService()

# --- Load Master Data ---
# Logic to find master-data.json. It's in app/static/master-data.json
# File is at app/agents/tools/concierge_tools.py
# So go up 3 levels: ../../../static/master-data.json
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MASTER_DATA_PATH = BASE_DIR / "app" / "static" / "master-data.json"

MASTER_DATA = {}
PARTY_TYPES_MAP: Dict[str, str] = {}
CASE_TYPES_MAP: Dict[str, str] = {}
COURT_LEVELS_MAP: Dict[str, str] = {}

def load_master_data():
    global MASTER_DATA, PARTY_TYPES_MAP, CASE_TYPES_MAP, COURT_LEVELS_MAP
    if not MASTER_DATA_PATH.exists():
        print(f"Warning: Master data file not found at {MASTER_DATA_PATH}")
        return

    try:
        with open(MASTER_DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            MASTER_DATA = data.get("master_data", {})
            
            # Create Case insensitive Mappings (Name -> ID)
            # Party Types
            for pt in MASTER_DATA.get("party_types", []):
                PARTY_TYPES_MAP[pt["name"].lower()] = pt["id"]
                
            # Case Types
            for ct in MASTER_DATA.get("case_types", []):
                CASE_TYPES_MAP[ct["name"].lower()] = ct["id"]

            # Court Levels
            for cl in MASTER_DATA.get("court_levels", []):
                COURT_LEVELS_MAP[cl["name"].lower()] = cl["id"]
                
    except Exception as e:
        print(f"Error loading master data: {e}")

load_master_data()

# Helper to look up ID
def get_id_from_name(mapping: Dict[str, str], name: str) -> Optional[str]:
    if not name:
        return None
    return mapping.get(name.lower().strip())

# --- Tools ---

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
    IMPORTANT: You MUST ask the user for the 'Party Type' before calling this tool.
    
    Args:
        company_id: Law firm ID.
        client_data: Dictionary containing client details.
                     Required Fields:
                     - 'fullName' (for Individual) OR 'companyName' (for Company).
                     - 'email'
                     - 'phone'
                     - 'partyType': One of valid Party Types (e.g., 'Individual', 'Private Limited Company', 'Partnership Firm').
                     - 'partyTypeId': (Optional) If you know the ID (e.g., PT_01).
                     
                     If 'partyType' is 'Individual' (or PT_01), use 'fullName'.
                     If 'partyType' is 'Company' or any other type, use 'companyName'.
    """
    # 1. Resolve Party Type ID
    party_type_name = client_data.get("partyType")
    party_type_id = client_data.get("partyTypeId")

    if not party_type_id and party_type_name:
        party_type_id = get_id_from_name(PARTY_TYPES_MAP, party_type_name)
    
    # Default to Individual if unknown (safe fallback or error?)
    if not party_type_id:
        # Check explicit clientType from legacy logic
        ctype = client_data.get("clientType", "").lower()
        if ctype == "individual":
            party_type_id = "PT_01"
        elif ctype == "company":
             # Try to pick a generic company type, or PT_03 (Private Ltd)
             party_type_id = "PT_03"
        else:
             # Default
             party_type_id = "PT_01" 

    # 2. Determine wrapper logic (Individual vs Company Client)
    # PT_01, PT_02 (HUF), PT_11 (Minor), PT_12 (Deceased) treated as 'Individual' schema-wise usually if they have names?
    # Actually schema distinguishes by `clientType` string: "individual" vs "company".
    # We need to map `partyTypeId` back to basic `clientType` for schema validation if strictly needed,
    # OR the Generic Client Create can handle it.
    # Looking at schemas: IndividualClient requires `fullName`. CompanyClient requires `companyName`.
    
    is_individual = party_type_id in ["PT_01", "PT_02", "PT_11", "PT_12"] # Heuristic
    
    # Inject partyTypeId
    client_data["partyTypeId"] = party_type_id
    
    try:
        if is_individual:
            client_data["clientType"] = "individual"
            # Ensure name fields
            if "fullName" not in client_data and "name" in client_data:
                client_data["fullName"] = client_data.pop("name")
            
            model = IndividualClient(**client_data)
        else:
            client_data["clientType"] = "company"
            if "companyName" not in client_data and "name" in client_data:
                client_data["companyName"] = client_data.pop("name")
                
            model = CompanyClient(**client_data)
            
        return client_service.create_client(company_id, model)
        
    except Exception as e:
        return f"Error validating client data: {str(e)}"

@tool
def create_new_case(company_id: str, client_id: str, case_data: dict):
    """
    Create a new case for a client.
    IMPORTANT: You MUST ask the user for 'Case Type' and 'Court Level' using valid standard names.

    Args:
        company_id: Law firm ID.
        client_id: The ID of the client.
        case_data: Dictionary containing case details.
                   Required Fields:
                   - 'caseName': Title of the case.
                   - 'caseType': One of standard types (e.g., 'Civil Suit', 'Writ Petition', 'Bail Application').
                   - 'courtLevel': One of standard levels (e.g., 'High Court', 'Supreme Court', 'District Court').
                   
                   Optional:
                   - 'caseTypeId': ID if known (e.g., CT_01).
                   - 'courtLevelId': ID if known (e.g., CL_HC).
                   - 'caseNumber': Filing number.
                   - 'openDate': YYYY-MM-DD.
    """
    try:
        # 1. Resolve IDs
        ct_name = case_data.get("caseType")
        ct_id = case_data.get("caseTypeId")
        
        if not ct_id and ct_name:
            ct_id = get_id_from_name(CASE_TYPES_MAP, ct_name)
        
        cl_name = case_data.get("courtLevel")
        cl_id = case_data.get("courtLevelId")
        
        if not cl_id and cl_name:
            cl_id = get_id_from_name(COURT_LEVELS_MAP, cl_name)
            
        # Inject IDs
        if ct_id:
            case_data["caseTypeId"] = ct_id
        if cl_id:
            case_data["courtLevelId"] = cl_id
            
        # Default missing fields
        if "caseSummary" not in case_data:
             case_data["caseSummary"] = "Created via AI Assistant"
             
        # Normalize Status
        if "status" in case_data:
             if isinstance(case_data["status"], str):
                 s = case_data["status"].lower()
                 if s == "ongoing": s = "active"
                 case_data["status"] = s
        else:
             case_data["status"] = "active"

        # Normalize Priority
        if "priority" in case_data and isinstance(case_data["priority"], str):
             case_data["priority"] = case_data["priority"].lower()
             
        # Normalize Fee Arrangement
        if "feeArrangement" in case_data:
             val = case_data["feeArrangement"]
             if isinstance(val, dict):
                 val = val.get("type", "hourly")
             if isinstance(val, str):
                 case_data["feeArrangement"] = val.lower()
             
        # Legacy Case Type fallback (if API still requires enum string)
        # We can set it to a safe default if strict validation is off, or try to map.
        if "caseType" not in case_data or case_data["caseType"] not in ["civil-litigation", "criminal-defense"]: 
            # The backend Pydantic model might enforce strict legacy Enum.
            # If so, we need to map CT_ID -> Legacy Enum.
            # For now, let's assume 'civil-litigation' as safe placeholder if not provided,
            # trusting `caseTypeId` is the source of truth for new features.
            if not case_data.get("caseType"):
                case_data["caseType"] = "civil-litigation"

        model = CaseCreate(**case_data)
        return case_service.create_case(company_id, client_id, model)
    except Exception as e:
        # Return a system error message that discourages immediate retries of the exact same invalid data
        return f"SYSTEM ERROR: Failed to create case. Reason: {str(e)}. \nSTOP. Do not retry with the exact same arguments. Ask the user for clarification or missing fields."

@tool
def get_master_data_options(category: str):
    """
    Get a list of valid options for a specific Master Data category.
    Use this when you need to know valid values for 'Party Type', 'Case Type', 'Court Level', or 'Document Type'.
    
    Args:
        category: One of 'party_types', 'case_types', 'court_levels', 'document_types'.
    """
    if category not in MASTER_DATA:
        # Try to fuzzy match common terms
        if "party" in category: category = "party_types"
        elif "case" in category: category = "case_types"
        elif "court" in category: category = "court_levels"
        elif "doc" in category: category = "document_types"
        else:
            return f"Invalid category. Available: {list(MASTER_DATA.keys())}"
            
    items = MASTER_DATA.get(category, [])
    # Return list of names
    return [item.get("name") for item in items]

concierge_tools = [search_clients, get_client_details, search_cases, create_new_client, create_new_case, get_master_data_options]
