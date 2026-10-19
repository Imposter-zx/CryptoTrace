"""Common exception types and HTTP error helpers."""
from __future__ import annotations

from fastapi import HTTPException, status


class CryptoTraceError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, error_code: str = "CRYPTOTRACE_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class NotFoundError(CryptoTraceError):
    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            f"{resource} with id '{resource_id}' was not found.",
            "NOT_FOUND",
        )
        self.resource = resource
        self.resource_id = resource_id


class ConflictError(CryptoTraceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "CONFLICT")


class ValidationError(CryptoTraceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "VALIDATION_ERROR")


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def raise_404(resource: str, resource_id: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "error_code": "NOT_FOUND",
            "message": f"{resource} '{resource_id}' not found.",
        },
    )


def raise_409(message: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"error_code": "CONFLICT", "message": message},
    )


def raise_422(message: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"error_code": "VALIDATION_ERROR", "message": message},
    )
