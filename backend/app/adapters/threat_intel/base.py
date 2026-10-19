"""
Threat intelligence adapter interface.
All threat intel providers must implement this protocol.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class ThreatIntelAdapter(ABC):
    """
    Abstract interface for threat intelligence providers.

    Phase 1: Interface only. Future implementations:
    - VirusTotal
    - OTX AlienVault
    - Shodan
    - etc.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @abstractmethod
    async def lookup_indicator(
        self, indicator: str, indicator_type: str
    ) -> Optional[dict[str, Any]]:
        """Look up a threat indicator (IP, hash, domain, URL)."""
        ...

    @abstractmethod
    async def get_file_report(self, file_hash: str) -> Optional[dict[str, Any]]:
        """Retrieve threat intelligence for a file hash."""
        ...

    def is_configured(self) -> bool:
        return False
