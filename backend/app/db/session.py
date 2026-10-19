"""SQLAlchemy async engine and session factory."""
from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    # Use NullPool in test environments to avoid issues with event loops
    # poolclass=NullPool,  # Uncomment for testing
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncSession:  # type: ignore[return]
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            if session.is_active:
                await session.commit()
        except Exception:
            try:
                if session.is_active:
                    await session.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                await session.close()
            except Exception:
                pass


async def init_db() -> None:
    """Verify database connectivity on startup. Migrations are managed by Alembic."""
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("database_connection_ok", url=_safe_url())
    except Exception as exc:
        logger.warning(
            "database_connection_failed",
            error=str(exc),
            hint="Run migrations and ensure PostgreSQL is running.",
        )
        # Do not crash on startup — health endpoint will report the status


def _safe_url() -> str:
    """Return the database URL with password masked."""
    url = settings.DATABASE_URL
    if "@" in url:
        scheme, rest = url.split("://", 1)
        userinfo, hostdb = rest.split("@", 1)
        if ":" in userinfo:
            user, _ = userinfo.split(":", 1)
            return f"{scheme}://{user}:***@{hostdb}"
    return url
