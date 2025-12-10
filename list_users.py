
import os
import sys

# Add app to path
sys.path.append(os.getcwd())

from app.repositories.company_repository import UserRepository

def list_users():
    print(f"--- Listing All Users ---")
    
    user_repo = UserRepository()
    
    # Scan the table (not efficient for large tables, but fine for debug)
    table = user_repo.table
    
    try:
        response = table.scan()
        items = response.get('Items', [])
        
        print(f"Found {len(items)} users:")
        for item in items:
            print(f"- {item.get('name', 'Unknown User')} ({item.get('email')}) [Company: {item.get('companyId')}]")
            
    except Exception as e:
        print(f"Failed to scan users: {e}")

if __name__ == "__main__":
    list_users()
