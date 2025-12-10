from typing import Optional, List
from boto3.dynamodb.conditions import Key
from app.repositories.base_repository import BaseRepository
from app.core.config import settings

class TemplateRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_TEMPLATES)

    def get_all_for_company(self, company_id: str) -> List[dict]:
        response = self.table.query(
            KeyConditionExpression=Key("companyId").eq(company_id)
        )
        return response.get("Items", [])

    def get_by_id(self, company_id: str, template_id: str) -> Optional[dict]:
        # This requires the full SK. If we don't have it, use get_by_id_scan.
        # But the base class get_by_id expects simple keys or we need to pass the full key.
        # Here we don't have the full key.
        return None

    def get_by_id_global(self, template_id: str) -> Optional[dict]:
        response = self.table.scan(
            FilterExpression=Key("templateId").eq(template_id)
        )
        items = response.get("Items", [])
        return items[0] if items else None

    def create(self, item: dict) -> dict:
        self.save(item)
        return item
