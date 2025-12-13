from app.services.core.document_service import DocumentService
from app.api.v1.schemas.document import DocumentCreate
import uuid

try:
    svc = DocumentService()
    # Mock data with NO category
    data = DocumentCreate(
        caseId="test-case-123",
        name="Test Doc.pdf",
        type="other",
        fileSize=1024,
        mimeType="application/pdf",
        documentCategoryId=None # Explicitly None
    )
    
    # We expect this to default to "general" internally before hitting DB
    # We can't easily mock the Repo/DB call here without complex mocks, 
    # but we can inspect `create_document_url` logic if we could import just that.
    # Actually, running this fully will try to hit DynamoDB and fail if credentials missing,
    # but that's what we want to test? No, user environment has failure on DB write.
    # The traceback showed ValidationException from DynamoDB.
    # If I run this, I might hit "No credentials" or similar if local setup is partial.
    # But wait, python code modification is what I did.
    # I can verify the logic by instantiating service and checking if I can mock repo.
    
    # Mock Repo
    class MockRepo:
        def create(self, item):
            print(f"Repo create called with: {item.get('documentCategoryId')}")
            if item.get('documentCategoryId') is None:
                 raise Exception("FAIL: documentCategoryId is None")
            else:
                 print("PASS: documentCategoryId is present")

    svc.repo = MockRepo()
    svc.case_repo = MockRepo() # Mock just to avoid init errors if any
    svc.s3 = MockRepo() # Mock s3
    
    # Mock S3 generate_presigned_url
    svc.s3.generate_presigned_url = lambda *args, **kwargs: "http://mock-url"

    svc.create_document_url("test-company", data)
    print("✅ Verification Passed")

except Exception as e:
    print(f"❌ Verification Failed: {e}")
    exit(1)
