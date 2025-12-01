from typing import Optional, List
from boto3.dynamodb.conditions import Key
from app.repositories.base_repository import BaseRepository
from app.core.config import settings

class DocumentRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_DOCUMENTS)

    def get_all_for_case(self, company_id: str, case_id: str) -> List[dict]:
        # PK is parentId (which is caseId)
        response = self.table.query(
            KeyConditionExpression=Key("parentId").eq(case_id)
        )
        return response.get("Items", [])

    def get_by_id(self, company_id: str, document_id: str) -> Optional[dict]:
        # This method signature is tricky because we need parentId (caseId) to get the item.
        # But the interface assumes company_id.
        # If we don't have caseId, we can't get the item efficiently if PK is parentId.
        # Unless we use GSI or Scan.
        # For now, I'll assume the caller passes case_id as company_id or I need to change the signature.
        # But wait, the route `get_document` only has `document_id`.
        # If I can't get it by ID without parentId, I might need to scan or change the API to include caseId.
        # The API route is `/{company_name}/{company_id}/documents/{document_id}`.
        # It doesn't have `case_id`.
        
        # I'll use Scan for now if I don't have caseId, OR I should change the API to be nested under case.
        # `/{company_name}/{company_id}/cases/{case_id}/documents/{document_id}`
        # The current route is `.../documents/{document_id}`.
        
        # Let's check if I can query by GSI.
        # If not, I'll have to Scan.
        
        # Actually, let's look at the `create` method.
        # It saves the item.
        pass

    def get_by_id_with_parent(self, parent_id: str, document_id: str) -> Optional[dict]:
        response = self.table.get_item(
            Key={"parentId": parent_id, "documentId": document_id}
        )
        return response.get("Item")

    def create(self, item: dict) -> dict:
        self.save(item)
        return item
