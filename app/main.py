from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import router as api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)
print("DEBUG: app/main.py loaded! -----------------------------------")

# Set all CORS enabled origins
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to Chambers IQ API"}

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import json

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )

from fastapi.responses import FileResponse
import os

@app.get("/api/master-data.json")
def get_master_data():
    file_path = os.path.join("app", "static", "master-data.json")
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/json")
    return JSONResponse(status_code=404, content={"detail": "Master data not found"})
