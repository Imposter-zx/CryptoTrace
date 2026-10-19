"""Health check endpoints — liveness and readiness."""
from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.schemas.investigations import HealthResponse

router = APIRouter(tags=["Health"])
logger = structlog.get_logger(__name__)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API v1 health check",
    description=(
        "Returns the application status and database connectivity. "
        "Use this endpoint for readiness probes."
    ),
)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Check application and database health."""
    db_status = "ok"
    db_detail: dict = {}

    try:
        result = await db.execute(text("SELECT version()"))
        row = result.fetchone()
        db_detail["version"] = row[0] if row else "unknown"
    except Exception as exc:
        db_status = "unavailable"
        db_detail["error"] = "Database connection failed. Check DATABASE_URL."
        logger.warning("health_check_db_failed", error=str(exc))

    overall_status = "ok" if db_status == "ok" else "degraded"

    return HealthResponse(
        status=overall_status,
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
        database=db_status,
        details={"database": db_detail} if db_detail else None,
    )
