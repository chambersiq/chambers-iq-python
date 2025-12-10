from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from app.services.core.company_service import CompanyService

router = APIRouter()

def get_company_service():
    return CompanyService()

@router.get("/companies/{company_id}/dashboard")
def get_dashboard_stats(
    company_id: str,
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
    service: CompanyService = Depends(get_company_service)
):
    print(f"API DEBUG: Dashboard stats request for {company_id} from {x_user_email}")
    try:
        stats = service.get_dashboard_stats(company_id)
        return stats
    except Exception as e:
        print(f"API DEBUG: Dashboard stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
