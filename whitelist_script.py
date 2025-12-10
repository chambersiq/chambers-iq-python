
import os
import sys
from datetime import datetime
import uuid

# Add app to path
sys.path.append(os.getcwd())

from app.services.core.company_service import UserService, CompanyService
from app.api.v1.schemas.company import UserCreate, CompanyCreate

def whitelist_user(email, name, company_id="chambers-iq-demo"):
    print(f"--- Whitelisting {email} ---")
    
    # 1. Ensure Company Exists
    comp_service = CompanyService()
    try:
        company = comp_service.get_company(company_id)
        if not company:
            print(f"Company {company_id} not found. Creating...")
            comp_service.create_company(CompanyCreate(
                name="Chambers IQ Demo Firm",
                email="admin@chambersiq.com",
                companyId=company_id
            ))
            print("Company created.")
        else:
            print(f"Company {company_id} found.")
    except Exception as e:
        print(f"Error checking company: {e}")
        return

    # 2. Add User
    user_service = UserService()
    
    # Check if user already exists
    existing = user_service.get_user_by_email_global(email)
    if existing:
        print(f"User {email} already exists: {existing}")
        return

    print(f"Creating user {email}...")
    new_user = UserCreate(
        email=email,
        name=name,
        role="admin"
    )
    
    try:
        result = user_service.create_user(company_id, new_user)
        print("User successfully whitelisted!")
        print(result)
    except Exception as e:
        print(f"Failed to create user: {e}")

if __name__ == "__main__":
    whitelist_user("ganesh.panaskar1@gmail.com", "Ganesh Panaskar")
