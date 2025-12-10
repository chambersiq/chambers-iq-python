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

