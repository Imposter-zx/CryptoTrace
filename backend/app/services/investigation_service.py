"""
Investigation service — business logic layer.
Services do not depend on HTTP or ORM internals.
"""
from __future__ import annotations

import math
import uuid
from typing import Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import raise_404
from app.db.repositories.investigations import InvestigationRepository
from app.models.investigations import Investigation, InvestigationStatus
from app.schemas.investigations import (
    InvestigationCreate,
    InvestigationListResponse,
    InvestigationResponse,
    InvestigationUpdate,
)

logger = structlog.get_logger(__name__)


def _to_response(inv: Investigation) -> InvestigationResponse:
    return InvestigationResponse(
        id=inv.id,
        title=inv.title,
        description=inv.description,
        status=inv.status,
        priority=inv.priority,
        tags=inv.tags,
        case_reference=inv.case_reference,
        is_archived=inv.is_archived,
        closed_at=inv.closed_at,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        evidence_count=len(inv.evidence) if inv.evidence else 0,
    )


class InvestigationService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = InvestigationRepository(db)

    async def create_investigation(
        self, data: InvestigationCreate
    ) -> InvestigationResponse:
        investigation = await self._repo.create(data)
        return _to_response(investigation)

    async def get_investigation(
        self, investigation_id: uuid.UUID
    ) -> InvestigationResponse:
        investigation = await self._repo.get_by_id(investigation_id)
        if not investigation:
            raise_404("Investigation", str(investigation_id))
        return _to_response(investigation)  # type: ignore[arg-type]

    async def list_investigations(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[InvestigationStatus] = None,
        search: Optional[str] = None,
    ) -> InvestigationListResponse:
        items, total = await self._repo.list(page, page_size, status, search)
        pages = math.ceil(total / page_size) if total > 0 else 0
        return InvestigationListResponse(
            items=[_to_response(inv) for inv in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def update_investigation(
        self, investigation_id: uuid.UUID, data: InvestigationUpdate
    ) -> InvestigationResponse:
        investigation = await self._repo.get_by_id(investigation_id)
        if not investigation:
            raise_404("Investigation", str(investigation_id))
        updated = await self._repo.update(investigation, data)  # type: ignore[arg-type]
        return _to_response(updated)

    async def delete_investigation(self, investigation_id: uuid.UUID) -> None:
        investigation = await self._repo.get_by_id(investigation_id)
        if not investigation:
            raise_404("Investigation", str(investigation_id))
        await self._repo.delete(investigation)  # type: ignore[arg-type]

    async def get_status_summary(self) -> dict[str, int]:
        return await self._repo.get_status_counts()
