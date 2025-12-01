import boto3
from botocore.exceptions import ClientError
import time

TABLE_NAME = "chambers-iq-beta-users"
REGION = "ap-south-1"

def delete_table():
    print(f"Deleting table '{TABLE_NAME}' in region '{REGION}'...")
    try:
        dynamodb = boto3.client('dynamodb', region_name=REGION)
        dynamodb.delete_table(TableName=TABLE_NAME)
        print("Delete request sent. Waiting for deletion...")
        
        waiter = dynamodb.get_waiter('table_not_exists')
        waiter.wait(TableName=TABLE_NAME)
        print("✅ Table deleted successfully.")
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("✅ Table does not exist (already deleted).")
        else:
            print(f"❌ Error deleting table: {e}")

if __name__ == "__main__":
    delete_table()
