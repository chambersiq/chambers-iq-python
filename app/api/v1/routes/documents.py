from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.services.core.document_service import DocumentService
from app.api.v1.schemas.document import Document, DocumentCreate

router = APIRouter()

def get_document_service():
    return DocumentService()

@router.get("/cases/{case_id}/documents", response_model=List[Document])
def get_documents(
    case_id: str, 
    service: DocumentService = Depends(get_document_service)
):
    # We need company_id for the service method (bad design in service but we can pass dummy or fix service)
    # The service method `get_documents(company_id, case_id)` uses repo `get_all_for_case(case_id)`.
    # It ignores company_id in the repo call (see DocumentRepository.get_all_for_case).
    # So we can pass any string for company_id.
    return service.get_documents("ignored", case_id)

@router.post("/companies/{company_id}/documents/upload-url", response_model=Dict[str, Any])
def create_upload_url(
    company_id: str, 
    doc_data: DocumentCreate, 
    service: DocumentService = Depends(get_document_service)
):
    doc, upload_url = service.create_document_url(company_id, doc_data)
    return {"document": doc, "uploadUrl": upload_url}

@router.get("/documents/{document_id}", response_model=Document)
def get_document(
    document_id: str, 
    service: DocumentService = Depends(get_document_service)
):
    doc = service.get_document("ignored", document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service)
):
    success = service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return None
