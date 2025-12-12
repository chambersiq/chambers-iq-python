from fastapi import Header, HTTPException, Path
from typing import Optional

async def verify_company_access(
    company_id: str = Path(..., description="Company ID from URL path"),
    x_company_id: Optional[str] = Header(None, alias="X-Company-Id")
):
    """
    Verifies that the requested company_id matches the authenticated user's company_id
    passed via X-Company-Id header (injected by Frontend Trusted Client).
    """
    if not x_company_id:
        raise HTTPException(
            status_code=401, 
            detail="Missing Authentication Context (X-Company-Id header required)"
        )

    if x_company_id != company_id:
        raise HTTPException(
            status_code=403, 
            detail=f"Access Denied: You do not have access to company {company_id}"
        )
    
    return x_company_id

async def get_current_user_email(
    x_user_email: Optional[str] = Header(None, alias="X-User-Email")
) -> str:
    """
    Extracts User Email from the trusted header.
    """
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Missing X-User-Email header")
    return x_user_email

async def get_current_company_id(
    x_company_id: Optional[str] = Header(None, alias="X-Company-Id")
) -> str:
    """
    Extracts Company ID from the trusted header.
    """
    if not x_company_id:
        raise HTTPException(status_code=401, detail="Missing X-Company-Id header")
    return x_company_id
