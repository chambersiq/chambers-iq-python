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
            "s3Key": s3_key,
            "url": "", # Placeholder, will be generated on get or set to s3 path
            "aiStatus": "queued" if data.generateSummary else "pending",
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
        # Use global lookup (Scan)
        item = self.repo.get_by_id_global(document_id)
        if item:
            item["url"] = self.s3.generate_presigned_url(item["s3Key"], method="get_object")
            return Document(**item)
        return None

    def delete_document(self, document_id: str) -> bool:
        doc = self.get_document("ignored", document_id)
        if not doc:
            return False
            
        # Delete from S3
        if doc.s3Key:
            self.s3.delete_file(doc.s3Key)
            
        # Delete from DB
        # We need the PK (parentId aka caseId) and SK (documentId)
        # But wait, DocumentRepository likely expects partition key and sort key.
        # Let's check DocumentRepository.delete method signature or if it exists.
        # Assuming it exists or I might need to add it.
        # Based on previous pattern, repositories usually take both keys.
        # But since we did a global lookup, we have the keys from 'doc'.
        # doc.caseId is mapped to 'parentId' in DB? 
        # In create_document_url: "parentId": data.caseId
        # So PK is caseId? 
        # Let's verify DocumentRepository.
        self.repo.delete(doc.caseId, document_id)
        return True

    def analyze_document(self, document_id: str, client_position: str = "Unknown") -> bool:
        doc = self.get_document("ignored", document_id)
        if not doc or not doc.s3Key:
            return False
            
        # 1. Fetch File
        file_content = self.s3.get_file_content(doc.s3Key)
        if not file_content:
            return False
            
        # 2. Extract Text
        text = ""
        try:
            if doc.name.lower().endswith(".pdf"):
                import io
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(file_content))
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            else:
                # Assume text/plain or similar
                text = file_content.decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"Extraction Error: {e}")
            self.repo.update(doc.caseId, document_id, {
                "aiStatus": "failed", 
                "aiSummary": f"Failed to extract text: {str(e)}"
            })
            return False

        if not text.strip():
             self.repo.update(doc.caseId, document_id, {
                "aiStatus": "failed", 
                "aiSummary": "Empty document text"
            })
             return False

        # 3. Run Agent
        try:
            from app.agents.document_summarizer import doc_analysis_app
            inputs = {
                "document_text": text,
                "client_position": client_position,
                "is_bundle": False
            }
            result = doc_analysis_app.invoke(inputs)
            
            # 4. Save Results
            updates = {
                "aiStatus": "completed",
                "aiSummary": result.get("final_advice", "")[:5000], 
                "description": result.get("final_advice", "")[:5000], # Overwrite user description with AI summary
                "extractedData": {
                    "category": result.get("category"),
                    "docType": result.get("doc_type"),
                    "scanQuality": result.get("scan_quality"),
                    "specialistAnalysis": result.get("specialist_analysis"),
                    "finalAdvice": result.get("final_advice"),
                    "isBundle": result.get("is_bundle")
                }
            }
            self.repo.update(doc.caseId, document_id, updates)
            return True
            
        except Exception as e:
            print(f"Agent Error: {e}")
            self.repo.update(doc.caseId, document_id, {
                "aiStatus": "failed", 
                "aiSummary": f"AI Error: {str(e)}"
            })
            return False
