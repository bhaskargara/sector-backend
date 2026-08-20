from fastapi import APIRouter

from app.api.routes.audit import router as audit_router
from app.api.routes.auth import router as auth_router
from app.api.routes.organization import router as organization_router
from app.api.routes.regulatory import router as regulatory_router

api_router = APIRouter()
api_router.include_router(audit_router)
api_router.include_router(auth_router)
api_router.include_router(organization_router)
api_router.include_router(regulatory_router)
