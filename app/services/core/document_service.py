from typing import List, Optional, Tuple
import uuid
from datetime import datetime
from app.repositories.document_repository import DocumentRepository
from app.repositories.case_repository import CaseRepository
from app.infrastructure.aws.s3_client import S3Client
from app.api.v1.schemas.document import Document, DocumentCreate
from app.core.config import settings

class DocumentService:
    def __init__(self):
        self.repo = DocumentRepository()
        self.case_repo = CaseRepository()
        self.s3 = S3Client()

    def create_document_url(self, company_id: str, data: DocumentCreate) -> Tuple[Document, str]:
        """
        Creates metadata and returns Document object + Presigned URL for upload.
        """
        # Validate allowed allowed types if categorization is active
        if data.documentTypeId:
            is_allowed = self.case_repo.validate_allowed_documents(company_id, data.caseId, data.documentTypeId)
            if not is_allowed:
                # We can log warning or block. For now, let's block to enforce rules.
                raise ValueError(f"Document Type {data.documentTypeId} is not allowed for this Case.")

        doc_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        s3_key = f"{company_id}/{data.caseId}/{doc_id}/{data.name}"
        
        # Generate Presigned URL
        presigned_url = self.s3.generate_presigned_url(s3_key, method="put_object", expiration=3600)
        
        # Construct URL (accessible after upload)
        
        doc_dict = data.model_dump()
        
        # Ensure documentCategoryId is set for GSI
        if not doc_dict.get("documentCategoryId"):
             doc_dict["documentCategoryId"] = "general"

        doc_dict.update({
            "parentId": data.caseId, # Set parentId for DynamoDB PK
            "companyId": company_id,
            "documentId": doc_id,
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
        # Scoped lookup
        item = self.repo.get_by_id(company_id, document_id)
        if item:
            item["url"] = self.s3.generate_presigned_url(item["s3Key"], method="get_object")
            return Document(**item)
        return None

    def delete_document(self, company_id: str, document_id: str) -> bool:
        doc = self.get_document(company_id, document_id)
        if not doc:
            return False
            
        # Delete from S3
        if doc.s3Key:
            self.s3.delete_file(doc.s3Key)
            
        # Delete from DB
        self.repo.delete(company_id, document_id)
        return True

    def analyze_document(self, document_id: str, client_position: str = "Unknown") -> bool:
        print(f"🔍 Starting document analysis for {document_id}")

        # Background task doesn't have company_id. Use global lookup (Scan SK).
        item = self.repo.get_by_id_global(document_id)
        if not item:
            print(f"❌ Document {document_id} not found in database")
            return False

        doc = Document(**item)
        if not doc.s3Key:
            print(f"❌ Document {document_id} has no S3 key")
            return False

        print(f"📄 Processing document: {doc.name} ({doc.originalName})")

        # 1. Fetch File
        file_content = self.s3.get_file_content(doc.s3Key)
        if not file_content:
            print(f"❌ Failed to download file from S3: {doc.s3Key}")
            return False

        print(f"📥 Downloaded {len(file_content)} bytes from S3")

        # 2. Process document using shared DocumentProcessor
        from app.services.lib.document_processor import DocumentProcessor

        processor = DocumentProcessor()
        result = processor.process_document(file_content, doc.name)

        # Log format detection results
        format_info = result.get("format", {})
        print(f"🔍 Detected format: {format_info.get('format_type', 'unknown')}")
        print(f"📋 Supported: {result.get('supported', False)}")
        print(f"📋 Scanned PDF: {format_info.get('is_scanned', False)}")
        print(f"📊 Quality Score: {result.get('quality_score', 0.0)}")
        print(f"📊 Word Count: {result.get('word_count', 0)}")

        # 3. Handle unsupported formats
        if not result["supported"]:
            format_type = result["format"].get("format_type")
            if format_type == "image":
                summary = "Image uploaded successfully. AI processing not supported for images yet."
            elif format_type == "pdf" and result["format"].get("is_scanned"):
                summary = "Scanned PDF uploaded successfully. AI processing not supported for scanned documents yet."
            else:
                summary = result["error_message"] or "File uploaded successfully. AI processing not supported for this format yet."

            self.repo.update(doc.companyId, document_id, {
                "aiStatus": "uploaded_only",  # Successfully uploaded, no AI processing
                "aiSummary": summary,
                "processingFormat": result["format"].get("format_type", "unknown"),
                "qualityScore": 0.0
            })
            return True  # Upload succeeded, just no AI processing

        # 4. Extract text and quality info
        text = result["text"]
        quality_score = result["quality_score"]

        # Log extracted text (first 500 chars to avoid binary data)
        text_preview = text[:500].replace('\n', ' ').replace('\r', ' ') if text else ""
        print(f"📄 Extracted text preview: {text_preview}...")
        print(f"📏 Total text length: {len(text) if text else 0} characters")

        if not text.strip():
             print(f"❌ Empty document text extracted")
             self.repo.update(doc.companyId, document_id, {
                "aiStatus": "failed",
                "aiSummary": "Empty document text",
                "qualityScore": 0.0
            })
             return False

        # 3. Run Agent
        try:
            from app.agents.workflows.summarization.document_summarizer import doc_analysis_app
            inputs = {
                "document_text": text,
                "client_position": client_position,
                "is_bundle": False
            }
            ai_result = doc_analysis_app.invoke(inputs)

            # 4. Save Results
            updates = {
                "aiStatus": "completed",
                "aiSummary": ai_result.get("final_advice", "")[:5000],
                "description": ai_result.get("final_advice", "")[:5000], # Overwrite user description with AI summary
                "qualityScore": quality_score,
                "processingFormat": result["format"].get("format_type", "unknown"),
                "extractedData": {
                    "category": ai_result.get("category"),
                    "docType": ai_result.get("doc_type"),
                    "scanQuality": ai_result.get("scan_quality"),
                    "specialistAnalysis": ai_result.get("specialist_analysis"),
                    "finalAdvice": ai_result.get("final_advice"),
                    "isBundle": ai_result.get("is_bundle")
                }
            }
            # Update using companyId as parentId in repo arguments
            self.repo.update(doc.companyId, document_id, updates)
            return True
            
        except Exception as e:
            print(f"Agent Error: {e}")
            self.repo.update(doc.companyId, document_id, {
                "aiStatus": "failed", 
                "aiSummary": f"AI Error: {str(e)}"
            })
            return False
