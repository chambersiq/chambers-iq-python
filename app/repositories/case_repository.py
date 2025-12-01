from typing import Optional, List
from boto3.dynamodb.conditions import Key
from app.repositories.base_repository import BaseRepository
from app.core.config import settings

from app.utils.dynamodb_utils import parse_float_to_decimal

class CaseRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_CASES)

    def get_all_for_client(self, company_id: str, client_id: str) -> List[dict]:
        pk = f"{company_id}#{client_id}"
        response = self.table.query(
            KeyConditionExpression=Key("companyId#clientId").eq(pk)
        )
        return response.get("Items", [])

    def get_all_for_company(self, company_id: str) -> List[dict]:
        # Scan with filter for MVP. In production, use GSI.
        response = self.table.scan(
            FilterExpression=Key("companyId").eq(company_id)
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

    def delete(self, company_id: str, client_id: str, case_id: str) -> None:
        pk = f"{company_id}#{client_id}"
        self.table.delete_item(
            Key={"companyId#clientId": pk, "caseId": case_id}
        )
