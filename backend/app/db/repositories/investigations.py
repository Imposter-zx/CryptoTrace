"""
Investigation repository — database access layer.
All queries go through parameterized ORM statements (no raw string interpolation).
"""
from __future__ import annotations

import math
import uuid
from typing import Optional

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investigations import Investigation, InvestigationStatus
from app.schemas.investigations import (
    InvestigationCreate,
    InvestigationListResponse,
    InvestigationResponse,
    InvestigationUpdate,
)

logger = structlog.get_logger(__name__)


class InvestigationRepository:
    """Encapsulates all database operations for investigations."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, data: InvestigationCreate) -> Investigation:
        investigation = Investigation(
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            tags=data.tags,
            case_reference=data.case_reference,
        )
        self._db.add(investigation)
        await self._db.flush()
        await self._db.refresh(investigation)
        logger.info("investigation_created", investigation_id=str(investigation.id))
        return investigation

    async def get_by_id(self, investigation_id: uuid.UUID) -> Optional[Investigation]:
        stmt = select(Investigation).where(
            Investigation.id == investigation_id,
            Investigation.is_archived == False,  # noqa: E712
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[InvestigationStatus] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Investigation], int]:
        base_stmt = select(Investigation).where(Investigation.is_archived == False)  # noqa: E712

        if status:
            base_stmt = base_stmt.where(Investigation.status == status)

        if search:
            search_term = f"%{search}%"
            base_stmt = base_stmt.where(
                Investigation.title.ilike(search_term)
                | Investigation.description.ilike(search_term)
                | Investigation.case_reference.ilike(search_term)
            )

        # Count total
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self._db.execute(count_stmt)
        total = total_result.scalar_one()

        # Paginate
        offset = (page - 1) * page_size
        stmt = (
            base_stmt.order_by(Investigation.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def update(
        self, investigation: Investigation, data: InvestigationUpdate
    ) -> Investigation:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(investigation, field, value)
        await self._db.flush()
        await self._db.refresh(investigation)
        logger.info("investigation_updated", investigation_id=str(investigation.id))
        return investigation

    async def delete(self, investigation: Investigation) -> None:
        """Soft-delete: mark as archived rather than destroying data."""
        investigation.is_archived = True
        await self._db.flush()
        logger.info(
            "investigation_archived",
            investigation_id=str(investigation.id),
        )

    async def hard_delete(self, investigation: Investigation) -> None:
        """Permanently remove from the database. Use with care."""
        await self._db.delete(investigation)
        await self._db.flush()
        logger.info(
            "investigation_hard_deleted",
            investigation_id=str(investigation.id),
        )

    async def get_status_counts(self) -> dict[str, int]:
        """Return investigation counts grouped by status."""
        stmt = (
            select(Investigation.status, func.count(Investigation.id))
            .where(Investigation.is_archived == False)  # noqa: E712
            .group_by(Investigation.status)
        )
        result = await self._db.execute(stmt)
        return {row[0].value: row[1] for row in result.all()}
