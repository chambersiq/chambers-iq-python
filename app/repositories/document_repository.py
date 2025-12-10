from typing import Optional, List
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from app.repositories.base_repository import BaseRepository
from app.core.config import settings

class DocumentRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_DOCUMENTS)

    def get_all_for_case(self, company_id: str, case_id: str) -> List[dict]:
        # Use GSI 'by_case'
        response = self.table.query(
            IndexName='by_case',
            KeyConditionExpression=Key("caseId").eq(case_id)
        )
        items = response.get("Items", [])
        # Filter by companyId for security
        return [i for i in items if i.get('companyId') == company_id]

    def get_by_id(self, company_id: str, document_id: str) -> Optional[dict]:
        # Keys: companyId, documentId
        response = self.table.get_item(
            Key={"companyId": company_id, "documentId": document_id}
        )
        return response.get("Item")

    def get_by_id_with_parent(self, parent_id: str, document_id: str) -> Optional[dict]:
        # Deprecated: parent_id was the old PK. Now we need companyId. 
        # This method assumes we don't have companyId.
        # We can scan or require companyId.
        # For compatibility, let's scan by documentId if possible as a fallback or return None.
        return self.get_by_id_global(document_id)

    def get_by_id_global(self, document_id: str) -> Optional[dict]:
        # Scan by documentId (SK). Not ideal but rare.
        # Alternatively create GSI on documentId if global lookup needed.
        response = self.table.scan(
            FilterExpression=Key("documentId").eq(document_id)
        )
        items = response.get("Items", [])
        return items[0] if items else None

    def create(self, item: dict) -> dict:
        self.save(item)
        return item

    def delete(self, parent_id: str, document_id: str) -> None:
        # 'parent_id' arg name legacy. It's actually company_id now.
        # We should rename the arg in interface, but for now treating as company_id
        # Wait, the interface in Service passes company_id?
        # Service: delete_document(document_id). It doesn't pass company_id. 
        # So service needs to fetch doc first to get company_id?
        # Yes.
        
        # If parent_id passed is actually company_id:
        self.table.update_item(
            Key={"companyId": parent_id, "documentId": document_id},
            UpdateExpression="SET archived = :val, updatedAt = :now",
            ExpressionAttributeValues={
                ":val": True,
                ":now": datetime.utcnow().isoformat()
            }
        )

    def update(self, parent_id: str, document_id: str, updates: dict) -> None:
        # parent_id here is company_id
        expr_parts = []
        expr_values = {}
        expr_names = {}
        
        updates["updatedAt"] = datetime.utcnow().isoformat()
        
        for k, v in updates.items():
            key_placeholder = f"#{k}"
            val_placeholder = f":{k}"
            expr_parts.append(f"{key_placeholder} = {val_placeholder}")
            expr_values[val_placeholder] = v
            expr_names[key_placeholder] = k
            
        self.table.update_item(
            Key={"companyId": parent_id, "documentId": document_id},
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeValues=expr_values,
            ExpressionAttributeNames=expr_names
        )

    def get_all_for_company(self, company_id: str, include_archived: bool = False) -> List[dict]:
        # Direct Query on PK
        response = self.table.query(
            KeyConditionExpression=Key("companyId").eq(company_id)
        )
        items = response.get("Items", [])
        
        if not include_archived:
            return [i for i in items if not i.get('archived')]
        return items

    def count_for_company(self, company_id: str) -> int:
        # Query Count
        response = self.table.query(
            KeyConditionExpression=Key("companyId").eq(company_id),
            Select='COUNT'
        )
        return response.get("Count", 0)

    def count_created_after(self, company_id: str, iso_date: str) -> int:
        response = self.table.query(
            KeyConditionExpression=Key("companyId").eq(company_id),
            FilterExpression=Attr("createdAt").gte(iso_date),
            Select='COUNT'
        )
        return response.get("Count", 0)


