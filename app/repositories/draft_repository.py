from typing import Optional, List
from boto3.dynamodb.conditions import Key, Attr
from app.repositories.base_repository import BaseRepository
from app.core.config import settings

class DraftRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_DRAFTS)

    def get_all_for_case(self, company_id: str, case_id: str) -> List[dict]:
        # PK is caseId
        response = self.table.query(
            KeyConditionExpression=Key("caseId").eq(case_id)
        )
        return response.get("Items", [])

    def get_by_id(self, case_id: str, draft_id: str) -> Optional[dict]:
        response = self.table.get_item(
            Key={"caseId": case_id, "draftId": draft_id}
        )
        return response.get("Item")

    def get_by_id_global(self, draft_id: str) -> Optional[dict]:
        response = self.table.scan(
            FilterExpression=Key("draftId").eq(draft_id)
        )
        items = response.get("Items", [])
        return items[0] if items else None

    def create(self, item: dict) -> dict:
        self.save(item)
        return item

    def update(self, case_id: str, draft_id: str, updates: dict) -> dict:
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
            Key={"caseId": case_id, "draftId": draft_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW"
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

    def delete(self, company_id: str, draft_id: str) -> None:
        self.table.update_item(
            Key={"companyId": company_id, "draftId": draft_id},
            UpdateExpression="SET archived = :val",
             ExpressionAttributeValues={
                ":val": True
            }
        )

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
