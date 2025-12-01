from abc import ABC, abstractmethod
from typing import List, Optional, Any
from app.infrastructure.aws.dynamodb_client import DynamoDBClient
from app.utils.dynamodb_utils import parse_float_to_decimal

class BaseRepository(ABC):
    def __init__(self, table_name: str):
        self.dynamodb = DynamoDBClient()
        self.table = self.dynamodb.get_table(table_name)

    def save(self, item: dict):
        item = parse_float_to_decimal(item)
        self.table.put_item(Item=item)
        return item

    def get(self, pk: str, sk: Optional[str] = None):
        key = {"pk": pk}  # Note: This needs to be adapted per table schema
        if sk:
            key["sk"] = sk
        
        response = self.table.get_item(Key=key)
        return response.get("Item")

    def delete(self, pk: str, sk: Optional[str] = None):
        key = {"pk": pk}
        if sk:
            key["sk"] = sk
        self.table.delete_item(Key=key)
