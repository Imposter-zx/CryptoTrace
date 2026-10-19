"""
Investigation CRUD endpoints.

All endpoints use dependency injection for session management.
Request size is implicitly limited by FastAPI/uvicorn defaults.
Stack traces are never returned to clients.
"""
from __future__ import annotations

import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.investigations import InvestigationStatus
from app.schemas.investigations import (
    InvestigationCreate,
    InvestigationListResponse,
    InvestigationResponse,
    InvestigationUpdate,
    MessageResponse,
)
from app.services.investigation_service import InvestigationService

router = APIRouter(prefix="/investigations", tags=["Investigations"])
logger = structlog.get_logger(__name__)


def get_service(db: AsyncSession = Depends(get_db)) -> InvestigationService:
    return InvestigationService(db)


@router.post(
    "",
    response_model=InvestigationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new investigation",
)
async def create_investigation(
    data: InvestigationCreate,
    service: InvestigationService = Depends(get_service),
) -> InvestigationResponse:
    return await service.create_investigation(data)


@router.get(
    "",
    response_model=InvestigationListResponse,
    summary="List investigations with pagination",
)
async def list_investigations(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status: Optional[InvestigationStatus] = Query(
        default=None, description="Filter by status"
    ),
    search: Optional[str] = Query(
        default=None, max_length=200, description="Search title, description, or case reference"
    ),
    service: InvestigationService = Depends(get_service),
) -> InvestigationListResponse:
    return await service.list_investigations(page, page_size, status, search)


@router.get(
    "/summary",
    summary="Get investigation status counts",
)
async def get_summary(
    service: InvestigationService = Depends(get_service),
) -> dict:
    counts = await service.get_status_summary()
    return {"status_counts": counts}


@router.get(
    "/{investigation_id}",
    response_model=InvestigationResponse,
    summary="Get a single investigation by ID",
)
async def get_investigation(
    investigation_id: uuid.UUID,
    service: InvestigationService = Depends(get_service),
) -> InvestigationResponse:
    return await service.get_investigation(investigation_id)


@router.patch(
    "/{investigation_id}",
    response_model=InvestigationResponse,
    summary="Update an investigation (partial update)",
)
async def update_investigation(
    investigation_id: uuid.UUID,
    data: InvestigationUpdate,
    service: InvestigationService = Depends(get_service),
) -> InvestigationResponse:
    return await service.update_investigation(investigation_id, data)


@router.delete(
    "/{investigation_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Archive (soft-delete) an investigation",
)
async def delete_investigation(
    investigation_id: uuid.UUID,
    service: InvestigationService = Depends(get_service),
) -> MessageResponse:
    await service.delete_investigation(investigation_id)
    return MessageResponse(message=f"Investigation {investigation_id} archived successfully.")
