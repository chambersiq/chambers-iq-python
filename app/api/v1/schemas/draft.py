from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DraftBase(BaseModel):
    name: str
    caseId: str
    clientId: str
    status: str = "draft"
    status: str = "draft"
    content: str
    archived: bool = False

class DraftCreate(DraftBase):
    pass

class DraftUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    archived: Optional[bool] = None
    caseId: Optional[str] = None # Should not change ideally but allowed
    clientId: Optional[str] = None


class Draft(DraftBase):
    companyId: str
    draftId: str
    caseName: Optional[str] = None # Denormalized
    clientName: Optional[str] = None # Denormalized
    lastEditedAt: str
    createdAt: str
