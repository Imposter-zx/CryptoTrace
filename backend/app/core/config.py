"""
Application configuration via environment variables.
All values are read from .env or the process environment.
No secrets are hardcoded.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "CryptoTrace AI"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Server ────────────────────────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://cryptotrace_user:changeme@localhost:5432/cryptotrace_db",
        description="Async database URL used by SQLAlchemy",
    )
    DATABASE_SYNC_URL: str = Field(
        default="postgresql+psycopg2://cryptotrace_user:changeme@localhost:5432/cryptotrace_db",
        description="Synchronous database URL used by Alembic",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:4173"

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="INSECURE_DEV_KEY_change_in_production",
        description="Must be overridden in all non-development environments",
    )

    # ── Blockchain / Etherscan Adapter ────────────────────────────────────────
    ETHERSCAN_API_KEY: str = ""
    ETHERSCAN_CHAIN_ID: int = 1
    ETHERSCAN_BASE_URL: str = "https://api.etherscan.io/v2/api"
    ETHERSCAN_TIMEOUT_SECONDS: float = 12.0
    ETHERSCAN_MAX_RETRIES: int = 3

    # ── Future adapters (empty until externally configured) ──────────────────
    BLOCKCHAIN_INFO_API_KEY: str = ""
    VIRUSTOTAL_API_KEY: str = ""
    SHODAN_API_KEY: str = ""
    OTXALIENVAULT_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"LOG_LEVEL must be one of {valid}")
        return upper

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
