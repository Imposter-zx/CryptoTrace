"""Pydantic schemas for Investigation CRUD operations."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.investigations import (
    EvidenceAssessment,
    EvidenceType,
    InvestigationPriority,
    InvestigationStatus,
    RelationshipType,
)


# ── Base ──────────────────────────────────────────────────────────────────────

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ── Investigation ─────────────────────────────────────────────────────────────

class InvestigationCreate(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255, description="Investigation title")
    description: Optional[str] = Field(None, max_length=10_000)
    status: InvestigationStatus = InvestigationStatus.DRAFT
    priority: InvestigationPriority = InvestigationPriority.MEDIUM
    tags: Optional[list[str]] = Field(None, description="Free-form tags")
    case_reference: Optional[str] = Field(None, max_length=100)

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be blank.")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is None:
            return v
        if len(v) > 50:
            raise ValueError("Maximum 50 tags per investigation.")
        return [tag.strip()[:100] for tag in v if tag.strip()]


class InvestigationUpdate(BaseSchema):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=10_000)
    status: Optional[InvestigationStatus] = None
    priority: Optional[InvestigationPriority] = None
    tags: Optional[list[str]] = None
    case_reference: Optional[str] = Field(None, max_length=100)
    analyst_notes: Optional[str] = Field(None, max_length=50_000)


class InvestigationResponse(BaseSchema):
    id: uuid.UUID
    title: str
    description: Optional[str]
    status: InvestigationStatus
    priority: InvestigationPriority
    tags: Optional[list[str]]
    case_reference: Optional[str]
    is_archived: bool
    closed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    evidence_count: int = 0


class InvestigationListResponse(BaseSchema):
    items: list[InvestigationResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ── Evidence ──────────────────────────────────────────────────────────────────

class EvidenceCreate(BaseSchema):
    evidence_type: EvidenceType
    title: str = Field(..., min_length=1, max_length=255)
    external_reference: Optional[str] = Field(None, max_length=512)
    raw_data: Optional[dict[str, Any]] = None
    normalized_data: Optional[dict[str, Any]] = None
    integrity_hash: Optional[str] = Field(None, max_length=128)
    assessment: EvidenceAssessment = EvidenceAssessment.UNVERIFIED
    assessment_rationale: Optional[str] = None
    collected_at: Optional[datetime] = None
    analyst_notes: Optional[str] = Field(None, max_length=50_000)
    source_id: Optional[uuid.UUID] = None


class EvidenceResponse(BaseSchema):
    id: uuid.UUID
    investigation_id: uuid.UUID
    evidence_type: EvidenceType
    title: str
    external_reference: Optional[str]
    assessment: EvidenceAssessment
    assessment_rationale: Optional[str]
    collected_at: Optional[datetime]
    analyst_notes: Optional[str]
    source_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime


# ── Shared response wrappers ──────────────────────────────────────────────────

class PaginationParams(BaseSchema):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class MessageResponse(BaseSchema):
    message: str


class HealthResponse(BaseSchema):
    status: str
    service: str
    version: str
    database: str
    details: Optional[dict[str, Any]] = None
