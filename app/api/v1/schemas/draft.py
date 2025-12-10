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

class Draft(DraftBase):
    companyId: str
    draftId: str
    caseName: Optional[str] = None # Denormalized
    clientName: Optional[str] = None # Denormalized
    lastEditedAt: str
    createdAt: str
