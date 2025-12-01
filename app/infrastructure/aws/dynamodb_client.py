import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

class DynamoDBClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DynamoDBClient, cls).__new__(cls)
            cls._instance.resource = boto3.resource(
                "dynamodb",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
        return cls._instance

    def get_table(self, table_name: str):
        return self.resource.Table(table_name)

dynamodb_client = DynamoDBClient()
