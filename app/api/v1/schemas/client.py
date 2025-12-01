from pydantic import BaseModel, EmailStr, Field, RootModel
from typing import Optional, List, Literal, Union
from datetime import datetime

class SecondaryContact(BaseModel):
    name: str
    title: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None

class ClientBase(BaseModel):
    clientType: Literal['individual', 'company']
    status: str = "active"
    
    # Common Address
    streetAddress: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zipCode: Optional[str] = None
    country: Optional[str] = None
    
    # Common Additional
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    referralSource: Optional[str] = None

class IndividualClient(ClientBase):
    clientType: Literal['individual']
    fullName: str
    email: EmailStr
    phone: str
    alternatePhone: Optional[str] = None
    dateOfBirth: Optional[str] = None
    gender: Optional[str] = None
    ssn: Optional[str] = None
    
    employerName: Optional[str] = None
    jobTitle: Optional[str] = None
    industry: Optional[str] = None
    
    preferredContactMethod: Optional[str] = None
    preferredLanguage: Optional[str] = None

class CompanyClient(ClientBase):
    clientType: Literal['company']
    companyName: str
    dbaName: Optional[str] = None
    companyType: Optional[str] = None
    taxId: Optional[str] = None
    industry: Optional[str] = None
    companySize: Optional[str] = None
    website: Optional[str] = None
    
    contactName: str
    contactTitle: Optional[str] = None
    contactEmail: EmailStr
    contactPhone: str
    contactAlternatePhone: Optional[str] = None
    
    registeredAgentName: Optional[str] = None
    registeredAgentAddress: Optional[str] = None
    stateOfIncorporation: Optional[str] = None
    
    secondaryContacts: Optional[List[SecondaryContact]] = []
    
    preferredContactMethod: Optional[str] = None
    billingContact: Optional[str] = None
    billingEmail: Optional[EmailStr] = None
    parentCompany: Optional[str] = None

class ClientCreate(RootModel):
    root: Union[IndividualClient, CompanyClient]

class Client(ClientBase):
    companyId: str
    clientId: str
    createdAt: str
    updatedAt: str
    totalCases: int = 0
    
    # Include fields from Individual/Company specific models that might be present
    # Since we are flattening, we need to be permissive or define a Union
    # For simplicity in response model, we can include all potential fields as optional
    # or use a more dynamic approach. Given the frontend expects specific types,
    # let's define a Union of the flattened types.

class ClientResponse(RootModel):
    root: Union[IndividualClient, CompanyClient]

# Actually, the cleanest way is to have the response model be a Union of 
# (IndividualClient + Metadata) and (CompanyClient + Metadata)

class ClientMetadata(BaseModel):
    companyId: str
    clientId: str
    createdAt: str
    updatedAt: str
    totalCases: int = 0

class IndividualClientResponse(IndividualClient, ClientMetadata):
    pass

class CompanyClientResponse(CompanyClient, ClientMetadata):
    pass

Client = Union[IndividualClientResponse, CompanyClientResponse]
