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
    isSystem: bool = False
    
    # Phase 2: Categorization
    documentTypeId: Optional[str] = None
    courtLevelId: Optional[str] = None
    caseTypeId: Optional[str] = None
    allowedCourtLevels: List[str] = []
    allowedCaseTypes: List[str] = []

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
