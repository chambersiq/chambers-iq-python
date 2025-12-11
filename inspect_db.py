import boto3
from dotenv import load_dotenv
import os

load_dotenv() # Load .env explicitly before importing settings or boto3 uses env vars

from app.core.config import settings
import json

def inspect_table():
    try:
        dynamodb = boto3.client('dynamodb', region_name=settings.AWS_REGION)
        table_name = settings.DYNAMODB_TABLE_CASES
        print(f"Inspecting table: {table_name}")
        
        response = dynamodb.describe_table(TableName=table_name)
        schema = response['Table']['KeySchema']
        print(json.dumps(schema, indent=2))
        
        attrs = response['Table']['AttributeDefinitions']
        print(json.dumps(attrs, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_table()
