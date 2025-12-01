from typing import Optional, List
from boto3.dynamodb.conditions import Key
from app.repositories.base_repository import BaseRepository
from app.core.config import settings

class DraftRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_DRAFTS)

    def get_all_for_case(self, company_id: str, case_id: str) -> List[dict]:
        # Query by companyId and filter by caseId
        response = self.table.query(
            KeyConditionExpression=Key("companyId").eq(company_id),
            FilterExpression=Key("caseId").eq(case_id)
        )
        return response.get("Items", [])

    def get_by_id(self, company_id: str, draft_id: str) -> Optional[dict]:
        response = self.table.get_item(
            Key={"companyId": company_id, "draftId": draft_id}
        )
        return response.get("Item")

    def create(self, item: dict) -> dict:
        self.save(item)
        return item

    def update(self, company_id: str, draft_id: str, updates: dict) -> dict:
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
            Key={"companyId": company_id, "draftId": draft_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW"
        )
        return response.get("Attributes")
