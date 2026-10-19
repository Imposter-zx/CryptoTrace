"""
CryptoTrace AI — Database Models

All models use:
- UUID primary keys
- Created/updated timestamps (UTC)
- Proper indexes and foreign-key constraints

Evidence integrity design:
- Raw observed facts are kept separate from analytical conclusions
- Confidence is extensible, not an arbitrary percentage
- Provenance is preserved per evidence record
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

# ── Enumerations ──────────────────────────────────────────────────────────────

import enum


class InvestigationStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    CLOSED = "closed"
    ARCHIVED = "archived"


class InvestigationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceType(str, enum.Enum):
    BLOCKCHAIN_TRANSACTION = "blockchain_transaction"
    WALLET_ADDRESS = "wallet_address"
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    FILE_HASH = "file_hash"
    MALWARE_SAMPLE = "malware_sample"
    THREAT_INTEL_INDICATOR = "threat_intel_indicator"
    EXCHANGE_RECORD = "exchange_record"
    NETWORK_ARTIFACT = "network_artifact"
    OTHER = "other"


class EvidenceAssessment(str, enum.Enum):
    """
    Extensible assessment of evidence quality.
    Deliberately avoids arbitrary percentages.
    Labels explain *why* rather than how confident we are.
    """
    UNVERIFIED = "unverified"          # Collected, not yet reviewed
    PROVIDER_SUPPLIED = "provider_supplied"  # Label from external provider, not independently confirmed
    CORROBORATED = "corroborated"      # Supported by multiple independent sources
    CONTRADICTED = "contradicted"      # Conflicts with other evidence
    ANALYST_CONFIRMED = "analyst_confirmed"  # Manually reviewed and confirmed by analyst
    ANALYST_REJECTED = "analyst_rejected"    # Manually reviewed and rejected


class RelationshipType(str, enum.Enum):
    LINKED_ADDRESS = "linked_address"
    TRANSACTION_FLOW = "transaction_flow"
    SHARED_ENTITY = "shared_entity"
    TEMPORAL_CORRELATION = "temporal_correlation"
    INFRASTRUCTURE_OVERLAP = "infrastructure_overlap"
    INVESTIGATES = "investigates"
    PART_OF = "part_of"


# ── Mixins ────────────────────────────────────────────────────────────────────

class TimestampMixin:
    """Adds created_at and updated_at to any model."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ── Models ────────────────────────────────────────────────────────────────────

class Investigation(Base, TimestampMixin):
    """
    Top-level container for a forensic investigation.

    An investigation groups related evidence, timelines, and analytical
    conclusions for a specific case.
    """

    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[InvestigationStatus] = mapped_column(
        Enum(InvestigationStatus, name="investigation_status"),
        default=InvestigationStatus.DRAFT,
        nullable=False,
        index=True,
    )
    priority: Mapped[InvestigationPriority] = mapped_column(
        Enum(InvestigationPriority, name="investigation_priority"),
        default=InvestigationPriority.MEDIUM,
        nullable=False,
        index=True,
    )
    # Tags stored as JSON array for flexible filtering
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    # Analyst-assigned reference number (optional, e.g. "CASE-2024-001")
    case_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence",
        back_populates="investigation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    relationships_as_source: Mapped[list["InvestigationRelationship"]] = relationship(
        "InvestigationRelationship",
        foreign_keys="InvestigationRelationship.source_investigation_id",
        back_populates="source_investigation",
        cascade="all, delete-orphan",
    )
    relationships_as_target: Mapped[list["InvestigationRelationship"]] = relationship(
        "InvestigationRelationship",
        foreign_keys="InvestigationRelationship.target_investigation_id",
        back_populates="target_investigation",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_investigations_status_priority", "status", "priority"),
        Index("ix_investigations_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Investigation id={self.id} title={self.title!r} status={self.status}>"


class EvidenceSource(Base, TimestampMixin):
    """
    Represents a data provider or collection method.

    Examples: Etherscan, VirusTotal, manual entry, internal OSINT.
    """

    __tablename__ = "evidence_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    adapter_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Maps to a registered adapter implementation.",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Source-level configuration (non-secret metadata only)
    config_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence",
        back_populates="source",
    )

    def __repr__(self) -> str:
        return f"<EvidenceSource name={self.name!r} adapter={self.adapter_key!r}>"


class Evidence(Base, TimestampMixin):
    """
    A single piece of observed evidence within an investigation.

    Design principles:
    - Raw observed facts are stored separately from analytical conclusions.
    - Confidence is expressed as an assessment label (not a percentage).
    - Provenance (source + external reference) is always recorded.
    - Integrity hash supports tamper detection.
    """

    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, name="evidence_type"),
        nullable=False,
        index=True,
    )
    # Human-readable label for this piece of evidence
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # External reference ID (e.g., transaction hash, IP, domain)
    external_reference: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, index=True
    )
    # The raw, unmodified data from the source (JSON blob)
    raw_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="Unmodified data as received from the source provider.",
    )
    # Normalized metadata for searching/indexing (analyst-populated)
    normalized_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True,
        comment="Normalized/structured form of raw_data for querying.",
    )
    # Integrity hash of the raw_data blob
    integrity_hash: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True,
        comment="SHA-256 or SHA-512 hash of raw_data for tamper detection.",
    )
    # Assessment / confidence label
    assessment: Mapped[EvidenceAssessment] = mapped_column(
        Enum(EvidenceAssessment, name="evidence_assessment"),
        default=EvidenceAssessment.UNVERIFIED,
        nullable=False,
        index=True,
    )
    # Assessment rationale — explains *why* the assessment was assigned
    assessment_rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # When was this evidence observed/collected (may differ from created_at)
    collected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Analyst notes
    analyst_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        back_populates="evidence",
    )
    source: Mapped[Optional["EvidenceSource"]] = relationship(
        "EvidenceSource",
        back_populates="evidence",
    )

    __table_args__ = (
        Index("ix_evidence_investigation_type", "investigation_id", "evidence_type"),
        Index("ix_evidence_assessment", "assessment"),
        Index("ix_evidence_collected_at", "collected_at"),
        Index(
            "uq_evidence_investigation_type_ref",
            "investigation_id",
            "evidence_type",
            "external_reference",
            unique=True,
            postgresql_where=text("external_reference IS NOT NULL"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Evidence id={self.id} type={self.evidence_type} "
            f"assessment={self.assessment}>"
        )


class InvestigationRelationship(Base, TimestampMixin):
    """
    Directional relationship between two investigations.

    Caution: A relationship records an *observed structural link*,
    not proof of common ownership or coordinated activity.
    """

    __tablename__ = "investigation_relationships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, name="relationship_type"),
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Analyst notes explaining the observed basis for this relationship
    analyst_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source_investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        foreign_keys=[source_investigation_id],
        back_populates="relationships_as_source",
    )
    target_investigation: Mapped["Investigation"] = relationship(
        "Investigation",
        foreign_keys=[target_investigation_id],
        back_populates="relationships_as_target",
    )

    __table_args__ = (
        UniqueConstraint(
            "source_investigation_id",
            "target_investigation_id",
            "relationship_type",
            name="uq_investigation_relationship",
        ),
        Index(
            "ix_inv_rel_source_target",
            "source_investigation_id",
            "target_investigation_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<InvestigationRelationship "
            f"{self.source_investigation_id} --{self.relationship_type}--> "
            f"{self.target_investigation_id}>"
        )
