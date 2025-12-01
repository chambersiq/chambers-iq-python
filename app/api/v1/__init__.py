from fastapi import APIRouter
from app.api.v1.routes import companies, clients, cases, documents, templates, drafts, users

api_router = APIRouter()

api_router.include_router(companies.router, tags=["companies"])
api_router.include_router(clients.router, tags=["clients"])
api_router.include_router(cases.router, tags=["cases"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(templates.router, tags=["templates"])
api_router.include_router(drafts.router, tags=["drafts"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
