from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentBase(BaseModel):
    caseId: str
    name: str
    fileSize: int
    mimeType: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    archived: bool = False

    # Phase 2: Required Indian Law Categorization (Legacy type field removed)
    documentTypeId: str
    documentCategoryId: str
    courtLevelId: str
    status: str = "draft"
    parentCaseTypeId: str

class DocumentCreate(DocumentBase):
    generateSummary: bool = False

class Document(DocumentBase):
    companyId: str
    documentId: str
    url: str
    s3Key: str
    
    # AI Analysis
    aiStatus: str = "pending"
    aiSummary: Optional[str] = None
    aiConfidence: Optional[float] = None
    extractedData: Optional[Dict[str, Any]] = None

    uploadedBy: Optional[str] = None
    createdAt: str
    updatedAt: str
