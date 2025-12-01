import boto3
import os
from botocore.exceptions import ClientError
from decimal import Decimal
import json

# Helper to handle Decimal serialization
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

REGION = os.getenv("AWS_REGION", "ap-south-1")
TABLE_NAME = os.getenv("DYNAMODB_TABLE_CLIENTS", "chambers-iq-beta-clients")

def scan_table():
    print(f"Scanning table '{TABLE_NAME}' in region '{REGION}'...")
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(TABLE_NAME)
        
        response = table.scan()
        items = response.get('Items', [])
        
        print(f"Found {len(items)} items:")
        for item in items:
            print(json.dumps(item, cls=DecimalEncoder, indent=2))
            
    except ClientError as e:
        print(f"❌ Error scanning table: {e}")

if __name__ == "__main__":
    scan_table()
