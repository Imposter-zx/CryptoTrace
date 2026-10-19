"""
Blockchain Adapter Protocol.
All blockchain data providers must implement this abstract interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class BlockchainAdapter(ABC):
    """
    Abstract interface for blockchain data providers.
    Ensures the investigation engine remains decoupled from any single vendor.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider (e.g. 'etherscan_v2')."""
        ...

    @property
    @abstractmethod
    def chain_id(self) -> int:
        """EIP-155 Chain ID for the targeted network (e.g. 1 for Ethereum Mainnet)."""
        ...

    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        """
        Retrieve raw transaction details by hash.
        Raises provider-specific exceptions on network, timeout, or API errors.
        """
        ...

    @abstractmethod
    async def get_address_transactions(
        self,
        address: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Retrieve native transactions involving the specified address.
        Returns empty list when no transactions exist.
        Raises on real provider failures.
        """
        ...

    @abstractmethod
    async def get_address_token_transfers(
        self,
        address: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Retrieve ERC-20 token transfer events involving the specified address.
        """
        ...

    @abstractmethod
    async def check_connectivity(self) -> dict[str, Any]:
        """
        Check connectivity and operational readiness of the provider without exposing credentials.
        """
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if required API credentials and base settings are present."""
        ...
