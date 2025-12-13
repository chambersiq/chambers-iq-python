from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class TemplateVariable(BaseModel):
    key: str
    label: str
    type: str
    description: Optional[str] = None

class TemplateBase(BaseModel):
    name: str
    description: str
    category: str
    content: str
    variables: Optional[List[TemplateVariable]] = []
    documentType: Optional[str] = None  # Specific type (e.g. "Values & Mission")
    caseType: Optional[str] = None      # Related case type (e.g. "civil-litigation")
    isSystem: bool = False

class TemplateCreate(TemplateBase):
    createdBy: Optional[str] = None

class Template(TemplateBase):
    companyId: str
    templateId: str
    createdAt: str
    updatedAt: str
    createdBy: Optional[str] = None

class TemplateGenerationRequest(BaseModel):
    generationId: str
    prompt: str


class WorkflowStartRequest(BaseModel):
    sampleDocs: List[str]
    companyId: str
    is_simulation: Optional[bool] = False

class WorkflowReviewRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None
