from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import List
from app.services.core.company_service import UserService
from app.api.v1.schemas.company import User

router = APIRouter()

def get_user_service():
    return UserService()

import logging

logger = logging.getLogger(__name__)

@router.get("/users/check-email", response_model=User)
def check_user_email(
    email: str = Query(..., description="Email to check"),
    service: UserService = Depends(get_user_service)
):
    """
    Check if a user exists by email.
    Used for authentication to verify if the logging-in user is registered.
    """
    logger.warning(f"API DEBUG: Request for email: {email}")
    logger.warning(f"API DEBUG: Using table: {service.user_repo.table.name}")
    
    # Enforce lowercase for PK lookup
    email_lower = email.lower()
    
    user = service.get_user_by_email_global(email_lower)
    logger.warning(f"API DEBUG: Lookup result: {user}")
    
    if not user:
        logger.warning(f"API DEBUG: User {email_lower} not found, raising 404. (Original: {email})")
        error_msg = f"User not found in table '{service.user_repo.table.name}'"
        raise HTTPException(status_code=404, detail=error_msg)
    return user

@router.get("/companies/{company_id}/users", response_model=List[User])
def get_users(
    company_id: str,
    service: UserService = Depends(get_user_service)
):
    return service.get_users(company_id)

from app.api.v1.schemas.company import UserCreate, UserUpdate

@router.post("/companies/{company_id}/users", response_model=User)
def create_user(
    company_id: str,
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    try:
        return service.create_user(company_id, user_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/users/{email}", response_model=User)
def update_user(
    email: str,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service)
):
    updated_user = service.update_user(email, user_data.model_dump())
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/users/{email}")
def delete_user(
    email: str,
    x_user_email: str = Header(..., alias="X-User-Email"),
    service: UserService = Depends(get_user_service)
):
    print(f"API DEBUG: DELETE request for {email} from requester {x_user_email}")
    try:
        service.delete_user(email, requester_email=x_user_email)
    except ValueError as e:
         print(f"API DEBUG: Delete failed with ValueError: {e}")
         raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
         print(f"API DEBUG: Delete failed with unexpected error: {e}")
         raise HTTPException(status_code=500, detail=str(e))
    return {"status": "success"}
