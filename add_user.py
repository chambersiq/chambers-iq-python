import boto3
from botocore.exceptions import ClientError
import uuid
from datetime import datetime

# Configuration
TABLE_NAME = "chambers-iq-beta-users-v2"
REGION = "ap-south-1"

USER_DATA = {
    "email": "ganesh.panaskar1@gmail.com",
    "companyId": "company-001",  # Default company
    "userId": str(uuid.uuid4()),
    "name": "Ganesh Panaskar",
    "role": "admin",
    "status": "active",
    "createdAt": datetime.utcnow().isoformat(),
    "updatedAt": datetime.utcnow().isoformat()
}

def add_user():
    print(f"Adding user '{USER_DATA['email']}' to table '{TABLE_NAME}'...")
    try:
        dynamodb = boto3.resource('dynamodb', region_name=REGION)
        table = dynamodb.Table(TABLE_NAME)
        
        table.put_item(Item=USER_DATA)
        print("✅ User added successfully.")
        print(f"Details: {USER_DATA}")
        
    except ClientError as e:
        print(f"❌ Error adding user: {e}")

if __name__ == "__main__":
    add_user()
