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

class Case(BaseEntity):
    companyId: str
    clientId: str
    caseId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caseName: str
    caseType: str
    description: Optional[str] = None
    status: str = "open"

class Document(BaseEntity):
    parentId: str
    documentId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    companyId: str
    parentType: str
    fileName: str
    s3Key: str
    mimeType: str
    fileSize: int

class Template(BaseEntity):
    companyId: str
    templateId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caseType: str
    templateName: str
    description: Optional[str] = None
    s3Key: str

class Draft(BaseEntity):
    caseId: str
    draftId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    companyId: str
    draftName: str
    content: str
    status: str = "draft"
