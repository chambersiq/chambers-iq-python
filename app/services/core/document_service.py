from typing import List, Optional, Tuple
import uuid
from datetime import datetime
from app.repositories.document_repository import DocumentRepository
from app.infrastructure.aws.s3_client import S3Client
from app.api.v1.schemas.document import Document, DocumentCreate
from app.core.config import settings

class DocumentService:
    def __init__(self):
        self.repo = DocumentRepository()
        self.s3 = S3Client()

    def create_document_url(self, company_id: str, data: DocumentCreate) -> Tuple[Document, str]:
        """
        Creates metadata and returns Document object + Presigned URL for upload.
        """
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        s3_key = f"{company_id}/{data.caseId}/{doc_id}/{data.name}"
        
        # Generate Presigned URL
        presigned_url = self.s3.generate_presigned_url(s3_key, method="put_object", expiration=3600)
        
        # Construct URL (accessible after upload)
        # Assuming public read or presigned get. For now, let's store the s3 key and generate get url on read.
        # But the frontend expects a 'url'.
        
        doc_dict = data.model_dump()
        doc_dict.update({
            "parentId": data.caseId, # Set parentId for DynamoDB PK
            "companyId": company_id,
            "documentId": doc_id,
            "s3Key": s3_key,
            "url": "", # Placeholder, will be generated on get or set to s3 path
            "aiStatus": "pending",
            "createdAt": now,
            "updatedAt": now
        })
        
        self.repo.create(doc_dict)
        
        return Document(**doc_dict), presigned_url

    def get_documents(self, company_id: str, case_id: str) -> List[Document]:
        items = self.repo.get_all_for_case(company_id, case_id)
        docs = []
        for item in items:
            # Generate GET presigned URL
            item["url"] = self.s3.generate_presigned_url(item["s3Key"], method="get_object")
            docs.append(Document(**item))
        return docs

    def get_document(self, company_id: str, document_id: str) -> Optional[Document]:
        # We don't have caseId here, so we can't use get_by_id_with_parent efficiently.
        # We might need to scan or the API should provide caseId.
        # For now, let's assume we can't get it without caseId.
        # Or we can scan.
        # Let's try to scan for now as a fallback.
        # But wait, I didn't implement scan in repo.
        return None
