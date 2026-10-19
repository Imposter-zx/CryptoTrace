"""Initial database schema for CryptoTrace AI Phase 1.

Revision ID: 20261013_0001
Revises: None
Create Date: 2026-10-13 17:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20261013_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Tables ─────────────────────────────────────────────────────────────────
    op.create_table(
        "investigations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "on_hold", "closed", "archived", name="investigation_status"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "priority",
            sa.Enum("low", "medium", "high", "critical", name="investigation_priority"),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("case_reference", sa.String(length=100), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_investigations_title", "investigations", ["title"])
    op.create_index("ix_investigations_status", "investigations", ["status"])
    op.create_index("ix_investigations_priority", "investigations", ["priority"])
    op.create_index("ix_investigations_case_reference", "investigations", ["case_reference"])
    op.create_index("ix_investigations_status_priority", "investigations", ["status", "priority"])
    op.create_index("ix_investigations_created_at", "investigations", ["created_at"])

    op.create_table(
        "evidence_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("adapter_key", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("config_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "investigation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investigations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evidence_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "evidence_type",
            sa.Enum(
                "blockchain_transaction",
                "wallet_address",
                "ip_address",
                "domain",
                "file_hash",
                "malware_sample",
                "threat_intel_indicator",
                "exchange_record",
                "network_artifact",
                "other",
                name="evidence_type",
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("external_reference", sa.String(length=512), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("normalized_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("integrity_hash", sa.String(length=128), nullable=True),
        sa.Column(
            "assessment",
            sa.Enum(
                "unverified",
                "provider_supplied",
                "corroborated",
                "contradicted",
                "analyst_confirmed",
                "analyst_rejected",
                name="evidence_assessment",
            ),
            nullable=False,
            server_default="unverified",
        ),
        sa.Column("assessment_rationale", sa.Text(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("analyst_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evidence_investigation_id", "evidence", ["investigation_id"])
    op.create_index("ix_evidence_source_id", "evidence", ["source_id"])
    op.create_index("ix_evidence_evidence_type", "evidence", ["evidence_type"])
    op.create_index("ix_evidence_external_reference", "evidence", ["external_reference"])
    op.create_index("ix_evidence_investigation_type", "evidence", ["investigation_id", "evidence_type"])
    op.create_index("ix_evidence_assessment", "evidence", ["assessment"])
    op.create_index("ix_evidence_collected_at", "evidence", ["collected_at"])

    op.create_table(
        "investigation_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "source_investigation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investigations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_investigation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("investigations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "relationship_type",
            sa.Enum(
                "linked_address",
                "transaction_flow",
                "shared_entity",
                "temporal_correlation",
                "infrastructure_overlap",
                "investigates",
                "part_of",
                name="relationship_type",
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("analyst_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "source_investigation_id",
            "target_investigation_id",
            "relationship_type",
            name="uq_investigation_relationship",
        ),
    )
    op.create_index("ix_investigation_relationships_relationship_type", "investigation_relationships", ["relationship_type"])
    op.create_index("ix_inv_rel_source_target", "investigation_relationships", ["source_investigation_id", "target_investigation_id"])


def downgrade() -> None:
    op.drop_table("investigation_relationships")
    op.drop_table("evidence")
    op.drop_table("evidence_sources")
    op.drop_table("investigations")
    op.execute("DROP TYPE IF EXISTS relationship_type")
    op.execute("DROP TYPE IF EXISTS evidence_assessment")
    op.execute("DROP TYPE IF EXISTS evidence_type")
    op.execute("DROP TYPE IF EXISTS investigation_priority")
    op.execute("DROP TYPE IF EXISTS investigation_status")
