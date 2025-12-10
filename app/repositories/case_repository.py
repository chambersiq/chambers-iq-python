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
        # Using Scan with filter to ensure consistency with get_all_for_company
        # and to bypass potential PK issues (since get_all_for_company works)
        response = self.table.scan(
            FilterExpression=Attr("companyId").eq(company_id) & Attr("clientId").eq(client_id)
        )
        return response.get("Items", [])

    def get_all_for_company(self, company_id: str, include_archived: bool = False) -> List[dict]:
        # Scan with filter for MVP. In production, use GSI.
        filter_expr = Key("companyId").eq(company_id)
        if not include_archived:
            filter_expr &= Attr("archived").ne(True)

        response = self.table.scan(
            FilterExpression=filter_expr
        )
        return response.get("Items", [])

    def get_by_id(self, company_id: str, client_id: str, case_id: str) -> Optional[dict]:
        pk = f"{company_id}#{client_id}"
        response = self.table.get_item(
            Key={"companyId#clientId": pk, "caseId": case_id}
        )
        return response.get("Item")

    def create(self, item: dict) -> dict:
        self.save(item)
        return item

    def update(self, company_id: str, client_id: str, case_id: str, updates: dict) -> dict:
        updates = parse_float_to_decimal(updates)
        pk = f"{company_id}#{client_id}"
        
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
            Key={"companyId#clientId": pk, "caseId": case_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW"
        )
        return response.get("Attributes")

    def get_by_id_scan(self, company_id: str, case_id: str) -> Optional[dict]:
        # Scan with filter for MVP. In production, use GSI.
        response = self.table.scan(
            FilterExpression=Key("companyId").eq(company_id) & Key("caseId").eq(case_id)
        )
        items = response.get("Items", [])
        return items[0] if items else None

    def get_by_id_global(self, case_id: str) -> Optional[dict]:
        response = self.table.scan(
            FilterExpression=Key("caseId").eq(case_id)
        )
        items = response.get("Items", [])
        return items[0] if items else None
    
    def get_all_by_client_global(self, client_id: str) -> List[dict]:
        response = self.table.scan(
            FilterExpression=Key("clientId").eq(client_id)
        )
        return response.get("Items", [])

    def delete(self, company_id: str, client_id: str, case_id: str) -> None:
        pk = f"{company_id}#{client_id}"
        self.table.update_item(
            Key={"companyId#clientId": pk, "caseId": case_id},
            UpdateExpression="SET archived = :val, updatedAt = :now",
            ExpressionAttributeValues={
                ":val": True,
                ":now": datetime.utcnow().isoformat()
            }
        )

    def count_for_company(self, company_id: str) -> int:
        # Scan with filter for MVP. In production, use GSI.
        response = self.table.scan(
            FilterExpression=Key("companyId").eq(company_id),
            Select='COUNT'
        )
        return response.get("Count", 0)

    def count_created_after(self, company_id: str, iso_date: str) -> int:
        response = self.table.scan(
            FilterExpression=Key("companyId").eq(company_id) & Attr("createdAt").gte(iso_date),
            Select='COUNT'
        )
        return response.get("Count", 0)
