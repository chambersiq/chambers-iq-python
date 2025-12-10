from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from app.services.core.document_service import DocumentService
from app.api.v1.schemas.document import Document, DocumentCreate

router = APIRouter()

def get_document_service():
    return DocumentService()

from app.api.v1.dependencies import verify_company_access
from fastapi import Header

@router.get("/cases/{case_id}/documents", response_model=List[Document])
def get_documents(
    case_id: str, 
    x_company_id: str = Header(..., alias="X-Company-Id"),
    service: DocumentService = Depends(get_document_service)
):
    # Pass company_id to service
    return service.get_documents(x_company_id, case_id)

@router.post("/companies/{company_id}/documents/upload-url", response_model=Dict[str, Any], dependencies=[Depends(verify_company_access)])
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
    x_company_id: str = Header(..., alias="X-Company-Id"),
    service: DocumentService = Depends(get_document_service)
):
    doc = service.get_document(x_company_id, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/documents/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    x_company_id: str = Header(..., alias="X-Company-Id"),
    service: DocumentService = Depends(get_document_service)
):
    success = service.delete_document(x_company_id, document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

@router.post("/documents/{document_id}/uploaded")
def confirm_upload(
    document_id: str,
    background_tasks: BackgroundTasks,
    x_company_id: str = Header(..., alias="X-Company-Id"),
    service: DocumentService = Depends(get_document_service)
):
    # We need company_id to securely fetch the document
    doc = service.get_document(x_company_id, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.aiStatus == "queued":
        background_tasks.add_task(service.analyze_document, document_id)
        return {"status": "processing_queued"}
        
    return {"status": "ok"}

@router.post("/documents/{document_id}/analyze")
def trigger_analysis(
    document_id: str,
    background_tasks: BackgroundTasks,
    x_company_id: str = Header(..., alias="X-Company-Id"),
    service: DocumentService = Depends(get_document_service)
):
    doc = service.get_document(x_company_id, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    background_tasks.add_task(service.analyze_document, document_id)
    return {"status": "processing_started"}
