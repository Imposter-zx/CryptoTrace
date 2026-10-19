"""
Pytest configuration and shared fixtures.
Integration tests require a running PostgreSQL instance.
Unit tests use mocks and do not require a database.
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient




# ── App fixture ───────────────────────────────────────────────────────────────

@pytest.fixture
def app() -> FastAPI:
    """Return a test application instance (no lifespan)."""
    from app.main import create_app
    test_app = create_app()
    return test_app


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """HTTP client for testing FastAPI routes."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
