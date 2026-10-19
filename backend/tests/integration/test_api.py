"""Integration tests for FastAPI endpoints."""
from __future__ import annotations

import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.db.session import get_db
from app.main import create_app
from app.models.investigations import (
    Investigation,
    InvestigationPriority,
    InvestigationStatus,
)


@pytest.fixture
def mock_db_session():
    """Mock database session for route testing without a live PostgreSQL instance."""
    session = AsyncMock()
    session.is_active = True
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def app_with_mock_db(mock_db_session):
    test_app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_db_session

    test_app.dependency_overrides[get_db] = override_get_db
    return test_app


@pytest.fixture
async def client_with_mock(app_with_mock_db) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app_with_mock_db),
        base_url="http://test",
    ) as ac:
        yield ac


class TestHealthEndpoints:
    @pytest.mark.anyio
    async def test_root_health(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == settings.APP_NAME

    @pytest.mark.anyio
    async def test_api_v1_health_database_ok(self, client_with_mock: AsyncClient, mock_db_session: AsyncMock):
        # Mock successful SELECT version()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = ["PostgreSQL 16.1 on x86_64"]
        mock_db_session.execute.return_value = mock_result

        response = await client_with_mock.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"
        assert data["details"]["database"]["version"] == "PostgreSQL 16.1 on x86_64"

    @pytest.mark.anyio
    async def test_api_v1_health_database_degraded(self, client_with_mock: AsyncClient, mock_db_session: AsyncMock):
        # Mock failed database execution
        mock_db_session.execute.side_effect = Exception("Connection refused")

        response = await client_with_mock.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["database"] == "unavailable"


class TestInvestigationEndpoints:
    @pytest.mark.anyio
    async def test_create_investigation(self, client_with_mock: AsyncClient, mock_db_session: AsyncMock):
        # Setup mock behavior
        test_id = uuid.uuid4()
        created_inv = Investigation(
            id=test_id,
            title="Operation Nightshade",
            description="Tracking darknet mixer flows",
            status=InvestigationStatus.ACTIVE,
            priority=InvestigationPriority.HIGH,
            tags=["mixer", "darknet"],
            case_reference="CASE-2026-001",
        )

        async def fake_refresh(obj):
            obj.id = test_id
            obj.created_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            obj.updated_at = obj.created_at
            obj.evidence = []
            obj.is_archived = False
            obj.closed_at = None

        mock_db_session.refresh.side_effect = fake_refresh

        payload = {
            "title": "Operation Nightshade",
            "description": "Tracking darknet mixer flows",
            "status": "active",
            "priority": "high",
            "tags": ["mixer", "darknet"],
            "case_reference": "CASE-2026-001",
        }
        response = await client_with_mock.post("/api/v1/investigations", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Operation Nightshade"
        assert data["status"] == "active"
        assert data["priority"] == "high"

    @pytest.mark.anyio
    async def test_create_investigation_validation_error(self, client_with_mock: AsyncClient):
        # Empty title should fail
        response = await client_with_mock.post(
            "/api/v1/investigations",
            json={"title": "   "},
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_list_investigations_empty(self, client_with_mock: AsyncClient, mock_db_session: AsyncMock):
        # Mock count result
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0

        # Mock items result
        mock_items_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_items_result.scalars.return_value = mock_scalars

        mock_db_session.execute.side_effect = [mock_count_result, mock_items_result]

        response = await client_with_mock.get("/api/v1/investigations")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    @pytest.mark.anyio
    async def test_get_investigation_not_found(self, client_with_mock: AsyncClient, mock_db_session: AsyncMock):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        missing_id = str(uuid.uuid4())
        response = await client_with_mock.get(f"/api/v1/investigations/{missing_id}")
        assert response.status_code == 404
        assert response.json()["detail"]["error_code"] == "NOT_FOUND"

    @pytest.mark.anyio
    async def test_get_investigation_summary(self, client_with_mock: AsyncClient, mock_db_session: AsyncMock):
        mock_result = MagicMock()
        mock_result.all.return_value = [
            (InvestigationStatus.ACTIVE, 3),
            (InvestigationStatus.DRAFT, 2),
        ]
        mock_db_session.execute.return_value = mock_result

        response = await client_with_mock.get("/api/v1/investigations/summary")
        assert response.status_code == 200
        data = response.json()
        assert "status_counts" in data
        assert data["status_counts"]["active"] == 3
        assert data["status_counts"]["draft"] == 2
