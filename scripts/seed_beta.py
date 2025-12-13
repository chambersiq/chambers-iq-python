
import sys
import os
import boto3
import uuid
from datetime import datetime

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

def seed_beta():
    print("Seeding Beta Environment...")
    
    # Force Beta Tables explicitly
    # Note: settings might load from .env which could be Prod or Beta. 
    # We will construct table names manually to be safe.
    
    PREFIX = "chambers-iq-beta"
    COMPANY_TABLE = f"{PREFIX}-companies"
    USER_TABLE = f"{PREFIX}-users"
    
    dynamodb = boto3.resource('dynamodb', region_name='ap-south-1')
    
    company_table = dynamodb.Table(COMPANY_TABLE)
    user_table = dynamodb.Table(USER_TABLE)
    
    # 1. Create Company
    company_id = str(uuid.uuid4())
    company_data = {
        'companyId': company_id,
        'name': 'Beta Test Company',
        'email': 'admin@betatest.com',
        'status': 'active',
        'createdAt': datetime.utcnow().isoformat()
    }
    
    print(f"Creating Company: {company_data['name']} ({company_id})")
    company_table.put_item(Item=company_data)
    
    # 2. Create User
    # User PK is email
    user_email = "ganesh.panaskar1@gmail.com"
    user_data = {
        'email': user_email,
        'userId': str(uuid.uuid4()),
        'companyId': company_id,
        'name': 'Ganesh Panaskar',
        'firstName': 'Ganesh', # Some schemas use name, some separate. Schema showed 'name'. I'll add firstName/lastName just in case.
        'lastName': 'Panaskar',
        'role': 'super_admin', # Requested role
        'status': 'active',
        'createdAt': datetime.utcnow().isoformat()
    }
    
    print(f"Creating User: {user_data['email']} as {user_data['role']}")
    user_table.put_item(Item=user_data)
    
    print("Seeding Complete!")

if __name__ == "__main__":
    seed_beta()
