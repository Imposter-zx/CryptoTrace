"""Add evidence idempotency index and seed Etherscan source.

Revision ID: 20261015_0002
Revises: 20261013_0001
Create Date: 2026-10-15 20:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20261015_0002"
down_revision: Union[str, None] = "20261013_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ETHERSCAN_SOURCE_ID = uuid.UUID("a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6")


def upgrade() -> None:
    # 1. Add partial unique index on evidence for idempotent imports
    op.create_index(
        "uq_evidence_investigation_type_ref",
        "evidence",
        ["investigation_id", "evidence_type", "external_reference"],
        unique=True,
        postgresql_where=sa.text("external_reference IS NOT NULL"),
    )

    # 2. Seed Etherscan v2 Evidence Source if it does not already exist
    evidence_sources_table = sa.table(
        "evidence_sources",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("display_name", sa.String),
        sa.column("description", sa.Text),
        sa.column("adapter_key", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("config_metadata", postgresql.JSONB),
    )

    # Safe insert that works across PostgreSQL environments
    op.execute(
        sa.text(
            """
            INSERT INTO evidence_sources (
                id, name, display_name, description, adapter_key, is_active, config_metadata, created_at, updated_at
            )
            VALUES (
                'a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6',
                'etherscan_ethereum_mainnet',
                'Etherscan (Ethereum Mainnet)',
                'Etherscan API V2 multichain provider for Ethereum Mainnet (Chain ID: 1)',
                'etherscan_v2',
                true,
                '{"chain_id": 1, "network": "ethereum_mainnet", "api_version": "v2"}'::jsonb,
                now(),
                now()
            )
            ON CONFLICT (name) DO NOTHING;
            """
        )
    )


def downgrade() -> None:
    # Remove seeded source
    op.execute(
        sa.text(
            "DELETE FROM evidence_sources WHERE name = 'etherscan_ethereum_mainnet';"
        )
    )
    # Drop partial unique index
    op.drop_index("uq_evidence_investigation_type_ref", table_name="evidence")
