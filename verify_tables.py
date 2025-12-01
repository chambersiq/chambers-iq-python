import boto3
import os
from botocore.exceptions import ClientError

# Load env vars manually if needed, or rely on sourced env
# We will source .env when running this

REGION = os.getenv("AWS_REGION", "ap-south-1")

def list_tables():
    print(f"Checking tables in region: {REGION}")
    try:
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        response = dynamodb.list_tables()
        tables = response.get('TableNames', [])
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f" - {table}")
        
        return tables
    except ClientError as e:
        print(f"❌ Error listing tables: {e}")
        return []

if __name__ == "__main__":
    list_tables()
