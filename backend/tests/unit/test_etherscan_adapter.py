"""
Unit tests for the Etherscan adapter — provider response parsing,
retry logic, rate-limit handling, and auth error mapping.
All tests use mocked HTTP transport; no real network calls are made.
"""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import pytest_asyncio

from app.adapters.blockchain.etherscan import (
    BlockchainProviderAuthError,
    BlockchainProviderError,
    BlockchainProviderRateLimitError,
    BlockchainResourceNotFoundError,
    EtherscanAdapter,
    sanitize_url,
)


# ── Helper factories ──────────────────────────────────────────────────────────

def _make_mock_response(payload: dict, status_code: int = 200) -> httpx.Response:
    """Build a fake httpx.Response with the given JSON body."""
    return httpx.Response(
        status_code=status_code,
        headers={"content-type": "application/json"},
        content=json.dumps(payload).encode(),
        request=httpx.Request("GET", "https://api.etherscan.io/v2/api"),
    )


def _adapter_with_response(response: httpx.Response) -> EtherscanAdapter:
    """Build a no-retry adapter backed by a single mock response."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(return_value=response)
    return EtherscanAdapter(
        api_key="test_key",
        max_retries=1,
        http_client=mock_client,
    )


def _adapter_with_responses(responses: list[httpx.Response]) -> EtherscanAdapter:
    """Build a multi-retry adapter that iterates through responses."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_client.get = AsyncMock(side_effect=responses)
    return EtherscanAdapter(
        api_key="test_key",
        max_retries=len(responses),
        http_client=mock_client,
    )


# ── sanitize_url ──────────────────────────────────────────────────────────────

class TestSanitizeUrl:
    def test_masks_apikey(self):
        url = "https://api.etherscan.io/v2/api?module=account&apikey=MYSECRETKEY123"
        result = sanitize_url(url)
        assert "MYSECRETKEY123" not in result
        # urlencode may percent-encode the asterisks; either way, the secret is gone
        assert "REDACTED" in result

    def test_no_apikey_unchanged(self):
        url = "https://api.etherscan.io/v2/api?module=account"
        result = sanitize_url(url)
        assert result == url

    def test_malformed_url_fallback(self):
        # Should not raise
        result = sanitize_url("not-a-valid-url?apikey=secret")
        assert "secret" not in result


# ── Successful responses ──────────────────────────────────────────────────────

class TestSuccessfulResponses:
    @pytest.mark.asyncio
    async def test_get_address_transactions_success(self):
        payload = {
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "hash": "0x" + "a" * 64,
                    "blockNumber": "12345678",
                    "timeStamp": "1620000000",
                    "from": "0x" + "b" * 40,
                    "to": "0x" + "c" * 40,
                    "value": "1000000000000000000",
                    "gasUsed": "21000",
                    "gasPrice": "1000000000",
                    "isError": "0",
                    "txreceipt_status": "1",
                }
            ],
        }
        adapter = _adapter_with_response(_make_mock_response(payload))
        result = await adapter.get_address_transactions("0x" + "b" * 40, limit=10)
        assert len(result) == 1
        assert result[0]["hash"] == "0x" + "a" * 64

    @pytest.mark.asyncio
    async def test_get_address_token_transfers_success(self):
        payload = {
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "hash": "0x" + "d" * 64,
                    "from": "0x" + "e" * 40,
                    "to": "0x" + "f" * 40,
                    "contractAddress": "0x" + "1" * 40,
                    "tokenName": "Tether USD",
                    "tokenSymbol": "USDT",
                    "tokenDecimal": "6",
                    "value": "1000000",
                }
            ],
        }
        adapter = _adapter_with_response(_make_mock_response(payload))
        result = await adapter.get_address_token_transfers("0x" + "e" * 40, limit=10)
        assert len(result) == 1
        assert result[0]["tokenSymbol"] == "USDT"

    @pytest.mark.asyncio
    async def test_get_transaction_by_hash_success(self):
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "hash": "0x" + "a" * 64,
                "from": "0x" + "b" * 40,
                "to": "0x" + "c" * 40,
                "value": "0xde0b6b3a7640000",  # 1 ETH
                "blockNumber": "0xbc614e",
            },
        }
        adapter = _adapter_with_response(_make_mock_response(payload))
        result = await adapter.get_transaction("0x" + "a" * 64)
        assert result["hash"] == "0x" + "a" * 64

    @pytest.mark.asyncio
    async def test_empty_transaction_list_treated_as_ok(self):
        """Etherscan returns status '0' with 'No transactions found' for empty wallets — not an error."""
        payload = {
            "status": "0",
            "message": "No transactions found",
            "result": [],
        }
        adapter = _adapter_with_response(_make_mock_response(payload))
        result = await adapter.get_address_transactions("0x" + "b" * 40, limit=10)
        assert result == []

    @pytest.mark.asyncio
    async def test_no_transactions_found_message_variant(self):
        """Another variant: status '0' with message in result field."""
        payload = {
            "status": "0",
            "message": "OK",
            "result": "No transactions found",
        }
        adapter = _adapter_with_response(_make_mock_response(payload))
        result = await adapter.get_address_transactions("0x" + "b" * 40, limit=10)
        assert result == []


# ── Error handling ─────────────────────────────────────────────────────────────

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_transaction_not_found(self):
        """eth_getTransactionByHash returning null result raises BlockchainResourceNotFoundError."""
        payload = {"jsonrpc": "2.0", "id": 1, "result": None}
        adapter = _adapter_with_response(_make_mock_response(payload))
        with pytest.raises(BlockchainResourceNotFoundError):
            await adapter.get_transaction("0x" + "a" * 64)

    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_auth_error(self):
        payload = {
            "status": "0",
            "message": "NOTOK",
            "result": "Invalid API Key",
        }
        adapter = _adapter_with_response(_make_mock_response(payload))
        with pytest.raises(BlockchainProviderAuthError):
            await adapter.get_address_transactions("0x" + "b" * 40, limit=10)

    @pytest.mark.asyncio
    async def test_rate_limit_payload_raises(self):
        payload = {
            "status": "0",
            "message": "NOTOK",
            "result": "Max rate limit reached",
        }
        # All retries get the same rate-limit response
        adapter = _adapter_with_responses([
            _make_mock_response(payload),
        ])
        with pytest.raises(BlockchainProviderRateLimitError):
            await adapter.get_address_transactions("0x" + "b" * 40, limit=10)

    @pytest.mark.asyncio
    async def test_http_429_raises_rate_limit(self):
        response = httpx.Response(
            status_code=429,
            headers={"content-type": "application/json"},
            content=b"{}",
            request=httpx.Request("GET", "https://api.etherscan.io/v2/api"),
        )
        adapter = _adapter_with_responses([response])
        with pytest.raises(BlockchainProviderRateLimitError):
            await adapter.get_address_transactions("0x" + "b" * 40, limit=10)

    @pytest.mark.asyncio
    async def test_http_500_raises_provider_error(self):
        response = httpx.Response(
            status_code=500,
            headers={"content-type": "text/plain"},
            content=b"Internal Server Error",
            request=httpx.Request("GET", "https://api.etherscan.io/v2/api"),
        )
        adapter = _adapter_with_responses([response])
        with pytest.raises(BlockchainProviderError):
            await adapter.get_address_transactions("0x" + "b" * 40, limit=10)

    @pytest.mark.asyncio
    async def test_malformed_json_raises(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=httpx.Response(
            status_code=200,
            headers={"content-type": "application/json"},
            content=b"{not valid json}",
            request=httpx.Request("GET", "https://api.etherscan.io/v2/api"),
        ))
        adapter = EtherscanAdapter(api_key="test", max_retries=1, http_client=mock_client)
        with pytest.raises(BlockchainProviderError, match="Malformed JSON"):
            await adapter.get_address_transactions("0x" + "b" * 40, limit=10)

    @pytest.mark.asyncio
    async def test_timeout_raises(self):
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(
            side_effect=httpx.TimeoutException("timed out", request=httpx.Request("GET", "https://api.etherscan.io/v2/api"))
        )
        adapter = EtherscanAdapter(api_key="test", max_retries=1, http_client=mock_client)
        from app.adapters.blockchain.etherscan import BlockchainProviderTimeoutError
        with pytest.raises(BlockchainProviderTimeoutError):
            await adapter.get_address_transactions("0x" + "b" * 40, limit=10)


# ── is_configured ─────────────────────────────────────────────────────────────

class TestIsConfigured:
    def test_configured_with_key(self):
        adapter = EtherscanAdapter(api_key="test_key")
        assert adapter.is_configured() is True

    def test_not_configured_empty_key(self):
        adapter = EtherscanAdapter(api_key="")
        assert adapter.is_configured() is False

    def test_not_configured_whitespace_key(self):
        adapter = EtherscanAdapter(api_key="   ")
        assert adapter.is_configured() is False


# ── check_connectivity ─────────────────────────────────────────────────────────

class TestCheckConnectivity:
    @pytest.mark.asyncio
    async def test_unconfigured_returns_safe_status(self):
        adapter = EtherscanAdapter(api_key="")
        result = await adapter.check_connectivity()
        assert result["operational_status"] == "unconfigured"
        assert result["is_configured"] is False
        # Ensure no actual credential value appears (the env var *name* is fine)
        assert result.get("key_present") is False

    @pytest.mark.asyncio
    async def test_configured_reachable(self):
        payload = {"jsonrpc": "2.0", "id": 1, "result": "0x10AAAAA"}
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(return_value=_make_mock_response(payload))
        adapter = EtherscanAdapter(api_key="test_key", max_retries=1, http_client=mock_client)
        result = await adapter.check_connectivity()
        assert result["operational_status"] == "reachable"
        assert "test_key" not in str(result)
