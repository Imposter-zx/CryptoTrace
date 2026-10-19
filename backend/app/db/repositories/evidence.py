"""
Evidence repository — database access layer for Evidence and EvidenceSource.

Idempotency contract:
- `get_or_create_evidence` fetches an existing record matching
  (investigation_id, evidence_type, external_reference) before inserting.
- On a race-condition UniqueViolation, it performs a read-and-return fallback
  rather than overwriting existing raw_data.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investigations import (
    Evidence,
    EvidenceAssessment,
    EvidenceSource,
    EvidenceType,
)

logger = structlog.get_logger(__name__)


class EvidenceRepository:
    """Encapsulates all database operations for Evidence and EvidenceSource."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    # ── EvidenceSource ────────────────────────────────────────────────────────

    async def get_source_by_adapter_key(self, adapter_key: str) -> Optional[EvidenceSource]:
        """Fetch the EvidenceSource row matching a given adapter key."""
        stmt = select(EvidenceSource).where(
            EvidenceSource.adapter_key == adapter_key,
            EvidenceSource.is_active == True,  # noqa: E712
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_source_by_id(self, source_id: uuid.UUID) -> Optional[EvidenceSource]:
        stmt = select(EvidenceSource).where(EvidenceSource.id == source_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    # ── Evidence ──────────────────────────────────────────────────────────────

    async def get_by_id(self, evidence_id: uuid.UUID) -> Optional[Evidence]:
        stmt = select(Evidence).where(Evidence.id == evidence_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_evidence_for_investigation(
        self,
        investigation_id: uuid.UUID,
        evidence_type: Optional[EvidenceType] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[Evidence]:
        """
        Fetch all evidence records for an investigation.
        Optionally filter by evidence_type.
        """
        stmt = (
            select(Evidence)
            .where(Evidence.investigation_id == investigation_id)
            .order_by(Evidence.collected_at.desc(), Evidence.created_at.desc())
        )
        if evidence_type is not None:
            stmt = stmt.where(Evidence.evidence_type == evidence_type)
        stmt = stmt.offset(offset).limit(limit)
        result = await self._db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_external_reference(
        self,
        investigation_id: uuid.UUID,
        evidence_type: EvidenceType,
        external_reference: str,
    ) -> Optional[Evidence]:
        """Lookup existing evidence by the partial-unique-index columns."""
        stmt = select(Evidence).where(
            Evidence.investigation_id == investigation_id,
            Evidence.evidence_type == evidence_type,
            Evidence.external_reference == external_reference,
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_evidence(
        self,
        *,
        investigation_id: uuid.UUID,
        evidence_type: EvidenceType,
        title: str,
        external_reference: Optional[str],
        raw_data: Optional[dict],
        normalized_data: Optional[dict],
        integrity_hash: Optional[str],
        assessment: EvidenceAssessment,
        assessment_rationale: Optional[str] = None,
        source_id: Optional[uuid.UUID] = None,
        collected_at: Optional[datetime] = None,
    ) -> tuple[Evidence, bool]:
        """
        Idempotent evidence insertion.

        Returns ``(evidence, created)`` where ``created`` is True for new
        records and False when an existing duplicate was found.

        Contract:
        - If a record matching (investigation_id, evidence_type, external_reference)
          already exists, it is returned unchanged — raw_data is NEVER overwritten.
        - On a concurrent UniqueViolation the fallback read path is used.
        """
        # Fast path: check before insert to avoid spurious IntegrityErrors.
        if external_reference is not None:
            existing = await self.get_by_external_reference(
                investigation_id=investigation_id,
                evidence_type=evidence_type,
                external_reference=external_reference,
            )
            if existing is not None:
                logger.debug(
                    "evidence_duplicate_skipped",
                    investigation_id=str(investigation_id),
                    evidence_type=evidence_type.value,
                    external_reference=external_reference,
                )
                return existing, False

        evidence = Evidence(
            investigation_id=investigation_id,
            source_id=source_id,
            evidence_type=evidence_type,
            title=title,
            external_reference=external_reference,
            raw_data=raw_data,
            normalized_data=normalized_data,
            integrity_hash=integrity_hash,
            assessment=assessment,
            assessment_rationale=assessment_rationale,
            collected_at=collected_at or datetime.now(timezone.utc),
        )
        self._db.add(evidence)
        try:
            await self._db.flush()
            await self._db.refresh(evidence)
            logger.info(
                "evidence_created",
                investigation_id=str(investigation_id),
                evidence_id=str(evidence.id),
                evidence_type=evidence_type.value,
                external_reference=external_reference,
            )
            return evidence, True

        except IntegrityError:
            # Race-condition: another concurrent request inserted the same record.
            await self._db.rollback()
            logger.debug(
                "evidence_race_duplicate",
                investigation_id=str(investigation_id),
                evidence_type=evidence_type.value,
                external_reference=external_reference,
            )
            if external_reference is not None:
                existing = await self.get_by_external_reference(
                    investigation_id=investigation_id,
                    evidence_type=evidence_type,
                    external_reference=external_reference,
                )
                if existing is not None:
                    return existing, False
            # Unexpected integrity failure — re-raise
            raise
