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
    # For now, if header is missing, we might want to allow it strictly for debugging 
    # OR reject it. Let's reject to be secure by default.
    # Exception: If running locally without frontend?
    
    if not x_company_id:
        # Check if we are in strict mode? 
        # For this refactor, let's enforce it. Use curl with -H "X-Company-Id: ..."
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
