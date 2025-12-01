from typing import Optional, List
from boto3.dynamodb.conditions import Key
from app.repositories.base_repository import BaseRepository
from app.core.config import settings

import logging

logger = logging.getLogger(__name__)

class ClientRepository(BaseRepository):
    def __init__(self):
        logger.warning(f"DEBUG: ClientRepository initializing with table: {settings.DYNAMODB_TABLE_CLIENTS}")
        super().__init__(settings.DYNAMODB_TABLE_CLIENTS)

    def get_all_for_company(self, company_id: str) -> List[dict]:
        logger.warning(f"DEBUG: Querying clients for companyId: {company_id}")
        response = self.table.query(
            KeyConditionExpression=Key("companyId").eq(company_id)
        )
        items = response.get("Items", [])
        logger.warning(f"DEBUG: Found {len(items)} clients")
        return items

    def get_by_id(self, company_id: str, client_id: str) -> Optional[dict]:
        response = self.table.get_item(
            Key={"companyId": company_id, "clientId": client_id}
        )
        return response.get("Item")

    def create(self, item: dict) -> dict:
        logger.warning(f"DEBUG: Creating client: {item}")
        self.save(item)
        return item

    def update(self, company_id: str, client_id: str, updates: dict) -> dict:
        # Construct UpdateExpression
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
            Key={"companyId": company_id, "clientId": client_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values,
            ReturnValues="ALL_NEW"
        )
        return response.get("Attributes")
