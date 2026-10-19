"""
Etherscan API V2 Adapter for Ethereum Mainnet.

Implements:
- Multichain API v2 endpoint (`https://api.etherscan.io/v2/api`) with `chainid=1`.
- Asynchronous HTTP client using httpx.
- Connection and read timeouts.
- Exponential backoff retry with jitter for transient 429/5xx errors.
- Explicit status field parsing (distinguishing empty results from true errors).
- Strict API key masking in logs and error messages.
"""
from __future__ import annotations

import asyncio
import random
import re
from typing import Any, Optional
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import httpx
import structlog

from app.adapters.blockchain.base import BlockchainAdapter
from app.core.config import settings

logger = structlog.get_logger(__name__)


class BlockchainProviderError(Exception):
    """Base exception for all blockchain provider failures."""
    pass


class BlockchainProviderRateLimitError(BlockchainProviderError):
    """Raised when provider rate limit is exceeded."""
    pass


class BlockchainProviderTimeoutError(BlockchainProviderError):
    """Raised when connection or read timeout occurs."""
    pass


class BlockchainProviderAuthError(BlockchainProviderError):
    """Raised on invalid or missing API key."""
    pass


class BlockchainResourceNotFoundError(BlockchainProviderError):
    """Raised when a specific transaction or block is not found."""
    pass


def sanitize_url(url: str) -> str:
    """Mask any apikey query parameter in URLs to prevent secret leakage in logs."""
    try:
        parts = urlsplit(url)
        query = parse_qs(parts.query)
        if "apikey" in query:
            query["apikey"] = ["***REDACTED***"]
        sanitized_query = urlencode(query, doseq=True)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, sanitized_query, parts.fragment))
    except Exception:
        return re.sub(r"apikey=[^&]+", "apikey=***REDACTED***", url)


class EtherscanAdapter(BlockchainAdapter):
    """
    Etherscan API V2 multichain client for Ethereum Mainnet (chainid=1).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        chain_id: int = 1,
        base_url: Optional[str] = None,
        timeout: float = 12.0,
        max_retries: int = 3,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else settings.ETHERSCAN_API_KEY
        self._chain_id = chain_id or settings.ETHERSCAN_CHAIN_ID
        self._base_url = (base_url or settings.ETHERSCAN_BASE_URL).rstrip("/")
        self._timeout = timeout or settings.ETHERSCAN_TIMEOUT_SECONDS
        self._max_retries = max_retries or settings.ETHERSCAN_MAX_RETRIES
        self._client = http_client

    @property
    def provider_name(self) -> str:
        return "etherscan_v2"

    @property
    def chain_id(self) -> int:
        return self._chain_id

    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is not None:
            return self._client
        return httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout, connect=5.0),
            headers={"Accept": "application/json", "User-Agent": "CryptoTrace-Forensics/0.1.0"},
        )

    async def _send_request(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Execute request with bounded retries, exponential backoff, and jitter.
        """
        req_params = dict(params)
        req_params["chainid"] = self._chain_id
        if self._api_key:
            req_params["apikey"] = self._api_key

        client = await self._get_client()
        owns_client = self._client is None

        attempt = 0
        last_error: Optional[Exception] = None

        try:
            while attempt < self._max_retries:
                attempt += 1
                try:
                    response = await client.get(self._base_url, params=req_params)

                    # Check for rate limiting status code
                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        wait_time = float(retry_after) if retry_after else (1.0 * (2 ** attempt) + random.uniform(0.1, 0.5))
                        logger.warning("etherscan_http_429", attempt=attempt, wait_time=wait_time)
                        if attempt < self._max_retries:
                            await asyncio.sleep(wait_time)
                            continue
                        raise BlockchainProviderRateLimitError("Etherscan API rate limit exceeded (HTTP 429).")

                    # Handle 5xx server errors
                    if response.status_code >= 500:
                        wait_time = 0.5 * (2 ** attempt) + random.uniform(0.1, 0.4)
                        logger.warning("etherscan_http_5xx", status_code=response.status_code, attempt=attempt)
                        if attempt < self._max_retries:
                            await asyncio.sleep(wait_time)
                            continue
                        raise BlockchainProviderError(f"Etherscan server error: HTTP {response.status_code}")

                    response.raise_for_status()

                    try:
                        data = response.json()
                    except Exception as json_err:
                        raise BlockchainProviderError(f"Malformed JSON response from Etherscan: {json_err}")

                    # Check if response payload contains an error or rate-limit message
                    if isinstance(data, dict):
                        # Account module style: { status: '0', message: 'NOTOK', result: '...' }
                        status_str = str(data.get("status", ""))
                        message_str = str(data.get("message", ""))
                        result_val = data.get("result")

                        if status_str == "0":
                            result_str = str(result_val)
                            # Empty result checks
                            if (
                                "No transactions found" in message_str
                                or "No transactions found" in result_str
                                or "No records found" in message_str
                                or "No records found" in result_str
                                or result_val == []
                            ):
                                return {"status": "1", "message": "OK", "result": []}

                            # Rate limit checks
                            if "Max rate limit reached" in result_str or "rate limit" in result_str.lower():
                                wait_time = 1.0 * (2 ** attempt) + random.uniform(0.1, 0.5)
                                logger.warning("etherscan_payload_ratelimit", attempt=attempt, wait_time=wait_time)
                                if attempt < self._max_retries:
                                    await asyncio.sleep(wait_time)
                                    continue
                                raise BlockchainProviderRateLimitError("Etherscan API rate limit reached.")

                            # Invalid API key checks
                            if "Invalid API Key" in result_str or "Missing/Invalid API Key" in result_str:
                                raise BlockchainProviderAuthError("Invalid or missing Etherscan API key.")

                            # General provider failure
                            raise BlockchainProviderError(f"Etherscan error: {message_str} — {result_str}")

                        # Proxy module style: { jsonrpc: '2.0', error: { code: ..., message: ... } }
                        if "error" in data:
                            err = data["error"]
                            raise BlockchainProviderError(f"Etherscan RPC error: {err}")

                    return data

                except httpx.TimeoutException as exc:
                    logger.warning("etherscan_timeout", attempt=attempt, error=str(exc))
                    last_error = BlockchainProviderTimeoutError(f"Etherscan request timed out after {self._timeout}s.")
                    if attempt < self._max_retries:
                        await asyncio.sleep(0.5 * (2 ** attempt))
                        continue
                    raise last_error

                except httpx.RequestError as exc:
                    logger.warning("etherscan_network_error", attempt=attempt, error=str(exc))
                    last_error = BlockchainProviderError(f"Etherscan network connection error: {exc}")
                    if attempt < self._max_retries:
                        await asyncio.sleep(0.5 * (2 ** attempt))
                        continue
                    raise last_error

            if last_error:
                raise last_error
            raise BlockchainProviderError("Etherscan request failed after maximum retries.")

        finally:
            if owns_client:
                await client.aclose()

    async def get_transaction(self, tx_hash: str) -> dict[str, Any]:
        """
        Retrieve raw transaction object using proxy eth_getTransactionByHash.
        """
        params = {
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": tx_hash,
        }
        data = await self._send_request(params)
        result = data.get("result")
        if not result or not isinstance(result, dict):
            raise BlockchainResourceNotFoundError(
                f"Transaction '{tx_hash}' not found on Ethereum Mainnet."
            )
        return result

    async def get_address_transactions(
        self,
        address: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Retrieve native transactions for a given wallet address.
        """
        # Etherscan uses 1-based page indexing
        page = (offset // limit) + 1
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": page,
            "offset": limit,
            "sort": "desc",
        }
        data = await self._send_request(params)
        result = data.get("result")
        if isinstance(result, list):
            return result
        return []

    async def get_address_token_transfers(
        self,
        address: str,
        *,
        limit: int = 25,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Retrieve ERC-20 token transfer events for a given wallet address.
        """
        page = (offset // limit) + 1
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": page,
            "offset": limit,
            "sort": "desc",
        }
        data = await self._send_request(params)
        result = data.get("result")
        if isinstance(result, list):
            return result
        return []

    async def check_connectivity(self) -> dict[str, Any]:
        """
        Verify connectivity and operational status without exposing secrets.
        Uses a lightweight eth_blockNumber proxy check.
        """
        is_conf = self.is_configured()
        res: dict[str, Any] = {
            "provider": self.provider_name,
            "chain_id": self._chain_id,
            "network": "ethereum_mainnet",
            "is_configured": is_conf,
            "key_present": is_conf,
            "base_url": self._base_url,
            "operational_status": "unconfigured" if not is_conf else "ready",
            "details": {},
        }

        if not is_conf:
            res["details"]["message"] = "ETHERSCAN_API_KEY environment variable is not configured."
            return res

        try:
            # Query latest block number
            data = await self._send_request({"module": "proxy", "action": "eth_blockNumber"})
            block_hex = data.get("result")
            block_num = int(block_hex, 16) if block_hex and isinstance(block_hex, str) else None
            res["operational_status"] = "reachable"
            res["details"] = {
                "latest_block_hex": block_hex,
                "latest_block_decimal": block_num,
                "latency_probe": "ok",
            }
        except BlockchainProviderRateLimitError:
            res["operational_status"] = "degraded"
            res["details"]["error"] = "Provider rate limit currently active."
        except BlockchainProviderAuthError:
            res["operational_status"] = "degraded"
            res["details"]["error"] = "Configured API key was rejected by Etherscan."
        except Exception as exc:
            res["operational_status"] = "degraded"
            res["details"]["error"] = f"Connectivity check failed: {exc}"

        return res
