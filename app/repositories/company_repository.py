from typing import Optional, List
from datetime import datetime
from boto3.dynamodb.conditions import Key
from app.repositories.base_repository import BaseRepository
from app.core.config import settings

class CompanyRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_COMPANIES)

    def get_by_id(self, company_id: str) -> Optional[dict]:
        response = self.table.get_item(Key={"companyId": company_id})
        return response.get("Item")

    def create(self, item: dict) -> dict:
        self.save(item)
        return item

import logging

logger = logging.getLogger(__name__)

class UserRepository(BaseRepository):
    def __init__(self):
        logger.warning(f"DEBUG: UserRepository initializing with table: {settings.DYNAMODB_TABLE_USERS}")
        logger.warning(f"DEBUG: AWS Region: {settings.AWS_REGION}")
        super().__init__(settings.DYNAMODB_TABLE_USERS)

    def get_by_email_global(self, email: str) -> Optional[dict]:
        logger.warning(f"DEBUG: Looking up email: {email} in table: {self.table.name}")
        # Direct GetItem since email is now the PK
        response = self.table.get_item(Key={"email": email})
        item = response.get("Item")
        logger.warning(f"DEBUG: Found item: {item}")
        return item

    def get_all_for_company(self, company_id: str, include_archived: bool = False) -> List[dict]:
        # Query using GSI 'by_company'
        filter_expr = Key("companyId").eq(company_id)
        if not include_archived:
            # Note: GSI Queries can support FilterExpression
            # However, boto3 conditions might be tricky with Key objects if attributes aren't keys.
            # 'archived' is a non-key attribute.
            pass # We will filter in python for GSI query simplicity or use FilterExpression with Attr

        response = self.table.query(
            IndexName="by_company",
            KeyConditionExpression=Key("companyId").eq(company_id)
        )
        items = response.get("Items", [])
        
        if not include_archived:
            return [i for i in items if not i.get('archived')]
        return items

    def create(self, item: dict) -> dict:
        self.save(item)
        return item

    def delete(self, email: str):
        self.table.update_item(
            Key={"email": email},
            UpdateExpression="SET archived = :val, updatedAt = :now",
            ExpressionAttributeValues={
                ":val": True,
                ":now": datetime.utcnow().isoformat()
            }
        )
