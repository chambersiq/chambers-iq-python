from typing import Optional, List
from boto3.dynamodb.conditions import Key, Attr
from app.repositories.base_repository import BaseRepository
from app.core.config import settings

from datetime import datetime
from app.utils.dynamodb_utils import parse_float_to_decimal

class CaseRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_CASES)

    def get_all_for_client(self, company_id: str, client_id: str) -> List[dict]:
        # Use GSI 'by_client'
        response = self.table.query(
            IndexName='by_client',
            KeyConditionExpression=Key("clientId").eq(client_id)
        )
        items = response.get("Items", [])
        
        # In case of GSI consistency delay or cross-tenant data (unlikely with random IDs, but good practice), filter
        # Although client IDs should be unique.
        return [i for i in items if i.get('companyId') == company_id]

    def get_all_for_company(self, company_id: str, include_archived: bool = False) -> List[dict]:
        # Direct Query on PK
        response = self.table.query(
            KeyConditionExpression=Key("companyId").eq(company_id)
        )
        items = response.get("Items", [])
        
        if not include_archived:
            return [i for i in items if not i.get('archived')]
        return items

    def get_by_id(self, company_id: str, client_id: str, case_id: str) -> Optional[dict]:
        # New PK is companyId, SK is caseId
        # client_id argument is legacy/ignored for lookup since we have direct PK access
        response = self.table.get_item(
            Key={"companyId": company_id, "caseId": case_id}
        )
        item = response.get("Item")
        
        # If client_id was provided (not empty), we could verify it, 
        # but since Service passes "" and we trust companyId+caseId uniqueness, just return item.
        if client_id and item and item.get('clientId') != client_id:
             return None
             
        return item

    def create(self, item: dict) -> dict:
        self.save(item)
        return item

    def update(self, company_id: str, client_id: str, case_id: str, updates: dict) -> dict:
        updates = parse_float_to_decimal(updates)
        
        update_expr = "SET "
        expr_attr_names = {}
        expr_attr_values = {}
        
        for key, value in updates.items():
            attr_name = f"#{key}"
            attr_value = f":{key}"
            update_expr += f"{attr_name} = {attr_value}, "
            expr_attr_names[attr_name] = key
            expr_attr_values[attr_value] = value
            
        update_expr = update_expr.rstrip(", ")
        
        response = self.table.update_item(
            Key={"companyId": company_id, "caseId": case_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW"
        )
        return response.get("Attributes")

    def get_by_id_scan(self, company_id: str, case_id: str) -> Optional[dict]:
        # Deprecated: Now we can just use get_item
        response = self.table.get_item(
            Key={"companyId": company_id, "caseId": case_id}
        )
        return response.get("Item")

    def get_by_id_global(self, case_id: str) -> Optional[dict]:
        # If we don't have companyId, we can't find it effectively without GSI or Scan.
        # But wait, caseId is SK. We need PK.
        # We can scan filtering by caseId (still slow but Global needs might be rare)
        # OR add a GSI for global lookups if needed.
        # For now, keep Scan.
        response = self.table.scan(
            FilterExpression=Key("caseId").eq(case_id)
        )
        items = response.get("Items", [])
        return items[0] if items else None
    
    def get_all_by_client_global(self, client_id: str) -> List[dict]:
        # Use GSI 'by_client'
        response = self.table.query(
            IndexName='by_client',
            KeyConditionExpression=Key("clientId").eq(client_id)
        )
        return response.get("Items", [])

    def delete(self, company_id: str, client_id: str, case_id: str) -> None:
        self.table.update_item(
            Key={"companyId": company_id, "caseId": case_id},
            UpdateExpression="SET archived = :val, updatedAt = :now",
            ExpressionAttributeValues={
                ":val": True,
                ":now": datetime.utcnow().isoformat()
            }
        )

    def count_for_company(self, company_id: str) -> int:
        # Query Count
        response = self.table.query(
            KeyConditionExpression=Key("companyId").eq(company_id),
            Select='COUNT'
        )
        return response.get("Count", 0)

    def count_created_after(self, company_id: str, iso_date: str) -> int:
        # We don't have a Sort Key on PK=companyId in Main Table (SK is caseId).
        # We can't query by date unless we have a GSI `by_company_date` or Filter.
        # However, Query with Filter is MUCH better than Scan.
        # We query ALL items for company, then filter.
        # OR we add a GSI `by_company` with SK `createdAt` as proposed?
        # WAIT: My proposal said: "PK: companyId, SK: caseId. GSI: by_client".
        # I did NOT create a GSI `by_company` with SK `createdAt`.
        # So `count_created_after` will do a Query(PK=companyId) + Filter(createdAt > date).
        # This reads all company items but only returns matching. Cost is proportional to company size, not table size. Accepted.
        
        response = self.table.query(
            KeyConditionExpression=Key("companyId").eq(company_id),
            FilterExpression=Attr("createdAt").gte(iso_date),
            Select='COUNT'
        )
        return response.get("Count", 0)
