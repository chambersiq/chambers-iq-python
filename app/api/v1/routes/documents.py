from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.services.core.document_service import DocumentService
from app.api.v1.schemas.document import Document, DocumentCreate

router = APIRouter()

def get_document_service():
    return DocumentService()

@router.get("/{company_id}/cases/{case_id}/documents", response_model=List[Document])
def get_documents(
    company_id: str, 
    case_id: str, 
    service: DocumentService = Depends(get_document_service)
):
    return service.get_documents(company_id, case_id)

@router.post("/{company_id}/documents/upload-url", response_model=Dict[str, Any])
def create_upload_url(
    company_id: str, 
    doc_data: DocumentCreate, 
    service: DocumentService = Depends(get_document_service)
):
    doc, upload_url = service.create_document_url(company_id, doc_data)
    return {"document": doc, "uploadUrl": upload_url}

@router.get("/{company_id}/documents/{document_id}", response_model=Document)
def get_document(
    company_id: str, 
    document_id: str, 
    service: DocumentService = Depends(get_document_service)
):
    doc = service.get_document(company_id, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
