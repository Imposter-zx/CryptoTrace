"""
Integration tests for blockchain API endpoints.

All Etherscan HTTP calls are mocked; no real network or database required.
The tests verify: routing, validation, response schemas, and error mapping.
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.adapters.blockchain.etherscan import (
    BlockchainProviderAuthError,
    BlockchainProviderRateLimitError,
    BlockchainResourceNotFoundError,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _etherscan_response(payload: dict, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode(),
        request=httpx.Request("GET", "https://api.etherscan.io/v2/api"),
    )


SAMPLE_ADDRESS = "0x" + "a" * 40
SAMPLE_TX_HASH = "0x" + "b" * 64


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def app() -> FastAPI:
    from app.main import create_app
    return create_app()


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ── /blockchain/status ─────────────────────────────────────────────────────────

class TestBlockchainStatus:
    @pytest.mark.asyncio
    async def test_status_unconfigured(self, client: AsyncClient):
        """Status endpoint reports unconfigured when no API key is set."""
        with patch(
            "app.api.v1.endpoints.blockchain.BlockchainService.get_status",
            new_callable=AsyncMock,
        ) as mock_status:
            from app.schemas.blockchain import BlockchainStatusResponse
            mock_status.return_value = BlockchainStatusResponse(
                provider="etherscan_v2",
                chain_id=1,
                network="ethereum_mainnet",
                is_configured=False,
                key_present=False,
                base_url="https://api.etherscan.io/v2/api",
                operational_status="unconfigured",
                details={"message": "API key not configured."},
            )
            response = await client.get("/api/v1/blockchain/status")
        assert response.status_code == 200
        data = response.json()
        assert data["operational_status"] == "unconfigured"
        assert data["is_configured"] is False
        # API key must never appear in response
        assert "api_key" not in json.dumps(data).lower()

    @pytest.mark.asyncio
    async def test_status_reachable(self, client: AsyncClient):
        with patch(
            "app.api.v1.endpoints.blockchain.BlockchainService.get_status",
            new_callable=AsyncMock,
        ) as mock_status:
            from app.schemas.blockchain import BlockchainStatusResponse
            mock_status.return_value = BlockchainStatusResponse(
                provider="etherscan_v2",
                chain_id=1,
                network="ethereum_mainnet",
                is_configured=True,
                key_present=True,
                base_url="https://api.etherscan.io/v2/api",
                operational_status="reachable",
                details={"latest_block_decimal": 18000000},
            )
            response = await client.get("/api/v1/blockchain/status")
        assert response.status_code == 200
        assert response.json()["operational_status"] == "reachable"


# ── /blockchain/tx/{tx_hash} ──────────────────────────────────────────────────

class TestGetTransaction:
    @pytest.mark.asyncio
    async def test_invalid_hash_returns_422(self, client: AsyncClient):
        response = await client.get("/api/v1/blockchain/tx/not-a-hash")
        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["error_code"] == "INVALID_TX_HASH"

    @pytest.mark.asyncio
    async def test_too_short_hash_returns_422(self, client: AsyncClient):
        response = await client.get("/api/v1/blockchain/tx/0x" + "a" * 63)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_valid_hash_success(self, client: AsyncClient):
        from app.schemas.blockchain import BlockchainResponseMeta, NormalizedTransaction, TransactionDetailResponse
        from datetime import datetime, timezone

        mock_resp = TransactionDetailResponse(
            tx_hash=SAMPLE_TX_HASH,
            meta=BlockchainResponseMeta(
                source_provider="etherscan_v2",
                chain_id=1,
                network="ethereum_mainnet",
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                item_count=1,
                is_truncated=False,
            ),
            transaction=NormalizedTransaction(
                tx_hash=SAMPLE_TX_HASH,
                from_address="0x" + "c" * 40,
                to_address="0x" + "d" * 40,
                value_wei="1000000000000000000",
                value_eth="1",
                status="success",
                source_provider="etherscan_v2",
                chain_id=1,
                retrieved_at=datetime.now(timezone.utc).isoformat(),
            ),
        )

        with patch(
            "app.api.v1.endpoints.blockchain.BlockchainService.get_transaction",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            response = await client.get(f"/api/v1/blockchain/tx/{SAMPLE_TX_HASH}")
        assert response.status_code == 200
        data = response.json()
        assert data["tx_hash"] == SAMPLE_TX_HASH

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, client: AsyncClient):
        with patch(
            "app.api.v1.endpoints.blockchain.BlockchainService.get_transaction",
            new_callable=AsyncMock,
            side_effect=BlockchainResourceNotFoundError("Transaction not found."),
        ):
            response = await client.get(f"/api/v1/blockchain/tx/{SAMPLE_TX_HASH}")
        assert response.status_code == 404
        assert response.json()["detail"]["error_code"] == "BLOCKCHAIN_NOT_FOUND"


# ── /blockchain/address/{address}/transactions ─────────────────────────────────

class TestAddressTransactions:
    @pytest.mark.asyncio
    async def test_invalid_address_returns_422(self, client: AsyncClient):
        response = await client.get("/api/v1/blockchain/address/not-an-address/transactions")
        assert response.status_code == 422
        assert response.json()["detail"]["error_code"] == "INVALID_ETHEREUM_ADDRESS"

    @pytest.mark.asyncio
    async def test_valid_address_returns_200(self, client: AsyncClient):
        from app.schemas.blockchain import AddressTransactionsResponse, BlockchainResponseMeta
        from datetime import datetime, timezone

        mock_resp = AddressTransactionsResponse(
            address=SAMPLE_ADDRESS,
            meta=BlockchainResponseMeta(
                source_provider="etherscan_v2",
                chain_id=1,
                network="ethereum_mainnet",
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                item_count=0,
                is_truncated=False,
            ),
            transactions=[],
        )
        with patch(
            "app.api.v1.endpoints.blockchain.BlockchainService.get_address_transactions",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            response = await client.get(f"/api/v1/blockchain/address/{SAMPLE_ADDRESS}/transactions")
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == SAMPLE_ADDRESS.lower() or SAMPLE_ADDRESS in data["address"]
        assert "transactions" in data

    @pytest.mark.asyncio
    async def test_rate_limit_returns_429(self, client: AsyncClient):
        with patch(
            "app.api.v1.endpoints.blockchain.BlockchainService.get_address_transactions",
            new_callable=AsyncMock,
            side_effect=BlockchainProviderRateLimitError("Rate limit exceeded."),
        ):
            response = await client.get(f"/api/v1/blockchain/address/{SAMPLE_ADDRESS}/transactions")
        assert response.status_code == 429
        assert response.json()["detail"]["error_code"] == "BLOCKCHAIN_RATE_LIMIT"

    @pytest.mark.asyncio
    async def test_auth_error_returns_503(self, client: AsyncClient):
        with patch(
            "app.api.v1.endpoints.blockchain.BlockchainService.get_address_transactions",
            new_callable=AsyncMock,
            side_effect=BlockchainProviderAuthError("Invalid API key."),
        ):
            response = await client.get(f"/api/v1/blockchain/address/{SAMPLE_ADDRESS}/transactions")
        assert response.status_code == 503
        assert response.json()["detail"]["error_code"] == "BLOCKCHAIN_AUTH_ERROR"


# ── /blockchain/address/{address}/token-transfers ─────────────────────────────

class TestAddressTokenTransfers:
    @pytest.mark.asyncio
    async def test_invalid_address_returns_422(self, client: AsyncClient):
        response = await client.get("/api/v1/blockchain/address/bad-addr/token-transfers")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_valid_address_returns_200(self, client: AsyncClient):
        from app.schemas.blockchain import AddressTokenTransfersResponse, BlockchainResponseMeta
        from datetime import datetime, timezone

        mock_resp = AddressTokenTransfersResponse(
            address=SAMPLE_ADDRESS,
            meta=BlockchainResponseMeta(
                source_provider="etherscan_v2",
                chain_id=1,
                network="ethereum_mainnet",
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                item_count=0,
                is_truncated=False,
            ),
            token_transfers=[],
        )
        with patch(
            "app.api.v1.endpoints.blockchain.BlockchainService.get_address_token_transfers",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            response = await client.get(f"/api/v1/blockchain/address/{SAMPLE_ADDRESS}/token-transfers")
        assert response.status_code == 200
        assert "token_transfers" in response.json()


# ── /blockchain/investigate ────────────────────────────────────────────────────

class TestInvestigate:
    @pytest.mark.asyncio
    async def test_invalid_target_returns_422(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/blockchain/investigate",
            json={"target": "not-valid"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_valid_address_creates_investigation(self, client: AsyncClient):
        inv_id = uuid.uuid4()
        from app.schemas.blockchain import (
            BlockchainInvestigateResponse,
            CytoscapeGraphResponse,
            GraphMeta,
        )

        mock_resp = BlockchainInvestigateResponse(
            investigation_id=inv_id,
            target=SAMPLE_ADDRESS,
            target_type="wallet_address",
            evidence_created_count=3,
            evidence_skipped_duplicates_count=0,
            transactions_count=3,
            token_transfers_count=0,
            graph=CytoscapeGraphResponse(
                nodes=[],
                edges=[],
                meta=GraphMeta(
                    total_nodes=0,
                    total_edges=0,
                    investigation_id=str(inv_id),
                ),
            ),
            warnings=[],
        )

        with patch(
            "app.api.v1.endpoints.blockchain.BlockchainService.investigate",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            response = await client.post(
                "/api/v1/blockchain/investigate",
                json={"target": SAMPLE_ADDRESS},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["target_type"] == "wallet_address"
        assert data["evidence_created_count"] == 3
        assert "graph" in data

    @pytest.mark.asyncio
    async def test_valid_tx_hash_creates_investigation(self, client: AsyncClient):
        inv_id = uuid.uuid4()
        from app.schemas.blockchain import (
            BlockchainInvestigateResponse,
            CytoscapeGraphResponse,
            GraphMeta,
        )

        mock_resp = BlockchainInvestigateResponse(
            investigation_id=inv_id,
            target=SAMPLE_TX_HASH,
            target_type="transaction_hash",
            evidence_created_count=1,
            evidence_skipped_duplicates_count=0,
            transactions_count=1,
            token_transfers_count=0,
            graph=CytoscapeGraphResponse(
                nodes=[],
                edges=[],
                meta=GraphMeta(total_nodes=0, total_edges=0),
            ),
            warnings=[],
        )

        with patch(
            "app.api.v1.endpoints.blockchain.BlockchainService.investigate",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            response = await client.post(
                "/api/v1/blockchain/investigate",
                json={"target": SAMPLE_TX_HASH},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["target_type"] == "transaction_hash"


# ── /blockchain/investigations/{id}/graph ─────────────────────────────────────

class TestInvestigationGraph:
    @pytest.mark.asyncio
    async def test_investigation_not_found_returns_404(self, client: AsyncClient):
        with patch(
            "app.api.v1.endpoints.blockchain.InvestigationRepository.get_by_id",
            new_callable=AsyncMock,
            return_value=None,
        ):
            response = await client.get(f"/api/v1/blockchain/investigations/{uuid.uuid4()}/graph")
        assert response.status_code == 404
        assert response.json()["detail"]["error_code"] == "INVESTIGATION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_graph_returned_for_known_investigation(self, client: AsyncClient):
        inv_id = uuid.uuid4()
        mock_inv = MagicMock()
        mock_inv.id = inv_id

        from app.schemas.blockchain import CytoscapeGraphResponse, GraphMeta

        mock_graph = CytoscapeGraphResponse(
            nodes=[],
            edges=[],
            meta=GraphMeta(total_nodes=0, total_edges=0, investigation_id=str(inv_id)),
        )

        with patch(
            "app.api.v1.endpoints.blockchain.InvestigationRepository.get_by_id",
            new_callable=AsyncMock,
            return_value=mock_inv,
        ), patch(
            "app.api.v1.endpoints.blockchain.BlockchainService.get_investigation_graph",
            new_callable=AsyncMock,
            return_value=mock_graph,
        ):
            response = await client.get(f"/api/v1/blockchain/investigations/{inv_id}/graph")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert "meta" in data
