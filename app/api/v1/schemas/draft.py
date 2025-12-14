from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DraftBase(BaseModel):
    name: str
    caseId: str
    clientId: str
    status: str = "draft"
    content: str
    archived: bool = False
    templateId: Optional[str] = None
    documentType: Optional[str] = "General"
    
    # Phase 2: Categorization
    documentTypeId: Optional[str] = None
    documentCategoryId: Optional[str] = None

class DraftCreate(DraftBase):
    pass

class DraftUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    archived: Optional[bool] = None
    caseId: Optional[str] = None # Should not change ideally but allowed
    clientId: Optional[str] = None
    templateId: Optional[str] = None
    documentType: Optional[str] = None
    documentTypeId: Optional[str] = None
    documentCategoryId: Optional[str] = None


class Draft(DraftBase):
    companyId: str
    draftId: str
    caseName: Optional[str] = None # Denormalized
    clientName: Optional[str] = None # Denormalized
    templateName: Optional[str] = None # Denormalized
    lastEditedAt: str
    createdAt: str

# AI Template Generation Schemas
class GenerateAITemplateRequest(BaseModel):
    case_id: str
    document_type: str

class GenerateAITemplateResponse(BaseModel):
    template_content: str
