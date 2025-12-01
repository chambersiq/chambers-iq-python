import boto3
from botocore.exceptions import ClientError
import os

# Configuration matching app/core/config.py
TABLE_NAME = "chambers-iq-beta-users"
REGION = "ap-south-1"
EMAIL = "ganesh.panaskar1@gmail.com"

def list_tables():
    print(f"Listing tables in region '{REGION}'...")
    try:
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        response = dynamodb.list_tables()
        print("Tables found:")
        for name in response.get('TableNames', []):
            print(f"- {name}")
    except ClientError as e:
        print(f"\n❌ Error listing tables: {e}")

def debug_env():
    print(f"Region configured in script: {REGION}")
    print(f"AWS_ACCESS_KEY_ID: {'*' * 5 if os.environ.get('AWS_ACCESS_KEY_ID') else 'Not Set'}")
    print(f"AWS_PROFILE: {os.environ.get('AWS_PROFILE', 'Not Set')}")
    
    try:
        sts = boto3.client('sts', region_name=REGION)
        identity = sts.get_caller_identity()
        print(f"Caller Identity: {identity['Arn']}")
        print(f"Account: {identity['Account']}")
    except ClientError as e:
        print(f"❌ Error getting caller identity: {e}")

def check_user_in_table(table_name):
    print(f"\nChecking table '{table_name}'...")
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(table_name)
        response = table.get_item(Key={'email': EMAIL})
        item = response.get('Item')
        if item:
            print(f"✅ User FOUND in {table_name}:")
            print(item)
            return True
        else:
            print(f"❌ User NOT FOUND in {table_name}.")
            return False
    except ClientError as e:
        print(f"❌ Error accessing {table_name}: {e}")
        return False

if __name__ == "__main__":
    debug_env()
    check_user_in_table("chambers-iq-beta-users-v2")
