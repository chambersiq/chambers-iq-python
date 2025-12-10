import boto3
from botocore.exceptions import ClientError
import uuid
from datetime import datetime

import os
from app.core.config import settings

# Configuration
TABLE_NAME = settings.DYNAMODB_TABLE_USERS
REGION = settings.AWS_REGION

# Get email from env or default
EMAIL = os.getenv("USER_EMAIL", "ganesh.panaskar1@gmail.com")

USER_DATA = {
    "email": EMAIL,
    "companyId": "company-001",  # Default company
    "userId": str(uuid.uuid4()),
    "name": "Admin User",
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
