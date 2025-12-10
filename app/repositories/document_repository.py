from typing import Optional, List
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
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

    def get_by_id_global(self, document_id: str) -> Optional[dict]:
        response = self.table.scan(
            FilterExpression=Key("documentId").eq(document_id)
        )
        items = response.get("Items", [])
        return items[0] if items else None

    def create(self, item: dict) -> dict:
        self.save(item)
        return item

    def delete(self, parent_id: str, document_id: str) -> None:
        self.table.update_item(
            Key={"parentId": parent_id, "documentId": document_id},
            UpdateExpression="SET archived = :val, updatedAt = :now",
            ExpressionAttributeValues={
                ":val": True,
                ":now": datetime.utcnow().isoformat()
            }
        )

    def get_all_for_company(self, company_id: str, include_archived: bool = False) -> List[dict]:
        # Scan with filter for MVP
        filter_expr = Key("companyId").eq(company_id)
        if not include_archived:
            filter_expr &= Attr("archived").ne(True)
            
        response = self.table.scan(
            FilterExpression=filter_expr
        )
        return response.get("Items", [])

    def count_for_company(self, company_id: str) -> int:
        # Scan with filter for MVP
        response = self.table.scan(
            FilterExpression=Key("companyId").eq(company_id) & Attr("archived").ne(True),
            Select='COUNT'
        )
        return response.get("Count", 0)

    def count_created_after(self, company_id: str, iso_date: str) -> int:
        response = self.table.scan(
            FilterExpression=Key("companyId").eq(company_id) & Attr("createdAt").gte(iso_date),
            Select='COUNT'
        )
        return response.get("Count", 0)
