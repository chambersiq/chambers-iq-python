from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.core.company_service import UserService
from app.api.v1.schemas.company import User

router = APIRouter()

def get_user_service():
    return UserService()

import logging

logger = logging.getLogger(__name__)

@router.get("/check-email", response_model=User)
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
    
    user = service.get_user_by_email_global(email)
    logger.warning(f"API DEBUG: Lookup result: {user}")
    
    if not user:
        logger.warning("API DEBUG: User not found, raising 404")
        error_msg = f"User not found in table '{service.user_repo.table.name}' (Region: {service.user_repo.table.meta.client.meta.region_name})"
        raise HTTPException(status_code=404, detail=error_msg)
    return user
