
from fastapi import APIRouter
from app.api.v1.routes import companies, clients, cases, documents, templates, drafts, users, dashboard, agent_workflows

router = APIRouter()
router.include_router(companies.router, tags=["Companies"])
router.include_router(clients.router, tags=["Clients"])
router.include_router(cases.router, tags=["Cases"])
router.include_router(documents.router, tags=["Documents"])
router.include_router(templates.router, tags=["Templates"])
router.include_router(drafts.router, tags=["Drafts"])
router.include_router(users.router, tags=["Users"])

router.include_router(dashboard.router, tags=["Dashboard"])
router.include_router(agent_workflows.router, prefix="/workflows", tags=["Agent Workflows"])

