from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class BaseEntity(BaseModel):
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class Company(BaseEntity):
    companyId: str
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str = "active"

class Client(BaseEntity):
    companyId: str
    clientId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str = "active"
    partyTypeId: Optional[str] = None # Added for Phase 2

class Case(BaseEntity):
    companyId: str
    clientId: str
    caseId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caseName: str
    # caseType: str # Removed
    description: Optional[str] = None
    status: str = "open"
    # Added for Phase 2
    courtLevelId: Optional[str] = None
    caseTypeId: Optional[str] = None
    practiceArea: Optional[str] = None
    primaryStatuteId: Optional[str] = None
    limitationYears: Optional[int] = None
    allowedDocTypeIds: List[str] = []
    reliefIds: List[str] = []

class Document(BaseEntity):
    parentId: str
    documentId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    companyId: str
    parentType: str
    fileName: str
    s3Key: str
    mimeType: str
    fileSize: int
    # Required for Indian Law Categorization (Phase 2)
    documentTypeId: str
    documentCategoryId: str
    courtLevelId: str
    status: str = "draft"
    parentCaseTypeId: str

class Template(BaseEntity):
    companyId: str
    templateId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    templateName: str
    description: Optional[str] = None
    s3Key: str
    # Indian Law Categorization (Phase 2) - Optional for existing templates, required for new ones
    documentTypeId: Optional[str] = None
    courtLevelId: Optional[str] = None
    caseTypeId: Optional[str] = None
    allowedCourtLevels: List[str] = []
    allowedCaseTypes: List[str] = []

class Draft(BaseEntity):
    caseId: str
    draftId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    companyId: str
    draftName: str
    content: str
    status: str = "draft"
    # Added for Phase 2
    documentTypeId: Optional[str] = None
    documentCategoryId: Optional[str] = None
