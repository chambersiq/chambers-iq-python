from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
import os

router = APIRouter()

@router.get("/master-data.json")
def get_master_data():
    file_path = os.path.join("app", "static", "master-data.json")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/json")
    return JSONResponse(status_code=404, content={"detail": "Master data not found"})
