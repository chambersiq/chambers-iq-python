from typing import Optional, List
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

    def get_all_for_company(self, company_id: str) -> List[dict]:
        # Query using GSI 'by_company'
        response = self.table.query(
            IndexName="by_company",
            KeyConditionExpression=Key("companyId").eq(company_id)
        )
        return response.get("Items", [])
