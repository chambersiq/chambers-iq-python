from typing import List, Optional
from boto3.dynamodb.conditions import Key
from app.repositories.base_repository import BaseRepository
from app.core.config import settings
from app.models.domain import Company, Client, Case, Document, Template, Draft

class CompanyRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_COMPANIES)

    def get_by_id(self, company_id: str) -> Optional[dict]:
        response = self.table.get_item(Key={"companyId": company_id})
        return response.get("Item")

class ClientRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_CLIENTS)

    def get_all_for_company(self, company_id: str) -> List[dict]:
        response = self.table.query(
            KeyConditionExpression=Key("companyId").eq(company_id)
        )
        return response.get("Items", [])

    def get_by_id(self, company_id: str, client_id: str) -> Optional[dict]:
        response = self.table.get_item(
            Key={"companyId": company_id, "clientId": client_id}
        )
        return response.get("Item")

class CaseRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_CASES)

    def get_all_for_client(self, company_id: str, client_id: str) -> List[dict]:
        pk = f"{company_id}#{client_id}"
        response = self.table.query(
            KeyConditionExpression=Key("companyId#clientId").eq(pk)
        )
        return response.get("Items", [])

    def get_by_id(self, company_id: str, client_id: str, case_id: str) -> Optional[dict]:
        pk = f"{company_id}#{client_id}"
        response = self.table.get_item(
            Key={"companyId#clientId": pk, "caseId": case_id}
        )
        return response.get("Item")

class DocumentRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_DOCUMENTS)

    def get_all_for_parent(self, parent_id: str) -> List[dict]:
        response = self.table.query(
            KeyConditionExpression=Key("parentId").eq(parent_id)
        )
        return response.get("Items", [])

class TemplateRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_TEMPLATES)

    def get_all_for_company(self, company_id: str) -> List[dict]:
        response = self.table.query(
            KeyConditionExpression=Key("companyId").eq(company_id)
        )
        return response.get("Items", [])

class DraftRepository(BaseRepository):
    def __init__(self):
        super().__init__(settings.DYNAMODB_TABLE_DRAFTS)

    def get_all_for_case(self, case_id: str) -> List[dict]:
        response = self.table.query(
            KeyConditionExpression=Key("caseId").eq(case_id)
        )
        return response.get("Items", [])
