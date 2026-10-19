"""API v1 router — aggregates all endpoint modules."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.blockchain import router as blockchain_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.investigations import router as investigations_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(investigations_router)
api_router.include_router(blockchain_router)
