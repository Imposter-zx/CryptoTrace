"""
Blockchain forensics API endpoints — Phase 2.

All endpoints:
- Use dependency injection for DB sessions and the blockchain service.
- Return structured error responses (never raw tracebacks).
- Never expose API keys or provider secrets in responses.
- Validate Ethereum addresses and transaction hashes before dispatching.
"""
from __future__ import annotations

import uuid
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.blockchain.etherscan import (
    BlockchainProviderAuthError,
    BlockchainProviderError,
    BlockchainProviderRateLimitError,
    BlockchainProviderTimeoutError,
    BlockchainResourceNotFoundError,
)
from app.db.repositories.evidence import EvidenceRepository
from app.db.repositories.investigations import InvestigationRepository
from app.db.session import get_db
from app.schemas.blockchain import (
    AddressTokenTransfersResponse,
    AddressTransactionsResponse,
    BlockchainInvestigateRequest,
    BlockchainInvestigateResponse,
    BlockchainStatusResponse,
    BoundedExpansionRequest,
    CytoscapeGraphResponse,
    TransactionDetailResponse,
)
from app.services.blockchain_service import BlockchainService
from app.utils.ethereum import (
    is_valid_ethereum_address,
    is_valid_tx_hash,
    validate_and_normalize_address,
    validate_and_normalize_tx_hash,
)

router = APIRouter(prefix="/blockchain", tags=["Blockchain"])
logger = structlog.get_logger(__name__)


# ── Dependency factories ───────────────────────────────────────────────────────

def get_blockchain_service() -> BlockchainService:
    """Inject the blockchain service (uses default EtherscanAdapter)."""
    return BlockchainService()


def get_evidence_repo(db: AsyncSession = Depends(get_db)) -> EvidenceRepository:
    return EvidenceRepository(db)


def get_investigation_repo(db: AsyncSession = Depends(get_db)) -> InvestigationRepository:
    return InvestigationRepository(db)


# ── Error mapping ─────────────────────────────────────────────────────────────

def _handle_provider_error(exc: BlockchainProviderError) -> HTTPException:
    """Map provider exceptions to HTTP errors without leaking secrets."""
    if isinstance(exc, BlockchainProviderAuthError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "BLOCKCHAIN_AUTH_ERROR",
                "message": "Blockchain provider authentication failed. Check API key configuration.",
            },
        )
    if isinstance(exc, BlockchainProviderRateLimitError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_code": "BLOCKCHAIN_RATE_LIMIT",
                "message": "Blockchain provider rate limit exceeded. Please retry after a short delay.",
            },
        )
    if isinstance(exc, BlockchainProviderTimeoutError):
        return HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error_code": "BLOCKCHAIN_TIMEOUT",
                "message": "Blockchain provider request timed out.",
            },
        )
    if isinstance(exc, BlockchainResourceNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "BLOCKCHAIN_NOT_FOUND",
                "message": str(exc),
            },
        )
    # Generic provider error — do not expose raw message which may contain internal details
    logger.error("blockchain_provider_error", error=str(exc))
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            "error_code": "BLOCKCHAIN_PROVIDER_ERROR",
            "message": "Blockchain provider returned an error. See server logs for details.",
        },
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get(
    "/status",
    response_model=BlockchainStatusResponse,
    summary="Check blockchain provider connectivity",
    description=(
        "Probe the configured blockchain provider (Etherscan) and return "
        "safe operational status information. API keys are never included in the response."
    ),
)
async def get_blockchain_status(
    service: BlockchainService = Depends(get_blockchain_service),
) -> BlockchainStatusResponse:
    try:
        return await service.get_status()
    except Exception as exc:
        logger.error("blockchain_status_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error_code": "BLOCKCHAIN_STATUS_ERROR",
                "message": "Could not determine blockchain provider status.",
            },
        )


@router.get(
    "/tx/{tx_hash}",
    response_model=TransactionDetailResponse,
    summary="Retrieve a transaction by hash",
    description=(
        "Fetch and normalize a single Ethereum transaction by its 0x-prefixed 64-hex-character hash."
    ),
)
async def get_transaction(
    tx_hash: str,
    service: BlockchainService = Depends(get_blockchain_service),
) -> TransactionDetailResponse:
    if not is_valid_tx_hash(tx_hash):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "INVALID_TX_HASH",
                "message": (
                    f"Invalid transaction hash '{tx_hash}'. "
                    "Expected a 0x-prefixed 64-character hex string."
                ),
            },
        )
    normalized_hash = validate_and_normalize_tx_hash(tx_hash)
    try:
        return await service.get_transaction(normalized_hash)
    except BlockchainProviderError as exc:
        raise _handle_provider_error(exc)


@router.get(
    "/address/{address}/transactions",
    response_model=AddressTransactionsResponse,
    summary="Retrieve native transactions for a wallet address",
)
async def get_address_transactions(
    address: str,
    limit: int = Query(default=25, ge=1, le=100, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    service: BlockchainService = Depends(get_blockchain_service),
) -> AddressTransactionsResponse:
    if not is_valid_ethereum_address(address):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "INVALID_ETHEREUM_ADDRESS",
                "message": f"Invalid Ethereum address: '{address}'.",
            },
        )
    normalized = validate_and_normalize_address(address)
    try:
        return await service.get_address_transactions(normalized, limit=limit, offset=offset)
    except BlockchainProviderError as exc:
        raise _handle_provider_error(exc)


@router.get(
    "/address/{address}/token-transfers",
    response_model=AddressTokenTransfersResponse,
    summary="Retrieve ERC-20 token transfers for a wallet address",
)
async def get_address_token_transfers(
    address: str,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: BlockchainService = Depends(get_blockchain_service),
) -> AddressTokenTransfersResponse:
    if not is_valid_ethereum_address(address):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error_code": "INVALID_ETHEREUM_ADDRESS",
                "message": f"Invalid Ethereum address: '{address}'.",
            },
        )
    normalized = validate_and_normalize_address(address)
    try:
        return await service.get_address_token_transfers(normalized, limit=limit, offset=offset)
    except BlockchainProviderError as exc:
        raise _handle_provider_error(exc)


@router.post(
    "/investigate",
    response_model=BlockchainInvestigateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a blockchain investigation",
    description=(
        "Investigate an Ethereum wallet address or transaction hash. "
        "Fetches real on-chain data, normalizes it, stores evidence in the database, "
        "and returns an evidence-backed Cytoscape.js graph."
    ),
)
async def investigate(
    request: BlockchainInvestigateRequest,
    service: BlockchainService = Depends(get_blockchain_service),
    evidence_repo: EvidenceRepository = Depends(get_evidence_repo),
    investigation_repo: InvestigationRepository = Depends(get_investigation_repo),
) -> BlockchainInvestigateResponse:
    try:
        return await service.investigate(
            request=request,
            evidence_repo=evidence_repo,
            investigation_repo=investigation_repo,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "INVESTIGATION_NOT_FOUND", "message": str(exc)},
        )
    except BlockchainProviderError as exc:
        raise _handle_provider_error(exc)
    except Exception as exc:
        logger.error("investigate_unexpected_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INVESTIGATION_ERROR",
                "message": "Investigation failed due to an internal error. Check server logs.",
            },
        )


@router.get(
    "/investigations/{investigation_id}/graph",
    response_model=CytoscapeGraphResponse,
    summary="Retrieve evidence-backed Cytoscape.js graph for an investigation",
)
async def get_investigation_graph(
    investigation_id: uuid.UUID,
    service: BlockchainService = Depends(get_blockchain_service),
    evidence_repo: EvidenceRepository = Depends(get_evidence_repo),
    investigation_repo: InvestigationRepository = Depends(get_investigation_repo),
) -> CytoscapeGraphResponse:
    # Verify investigation exists
    inv = await investigation_repo.get_by_id(investigation_id)
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "INVESTIGATION_NOT_FOUND",
                "message": f"Investigation '{investigation_id}' not found.",
            },
        )
    try:
        return await service.get_investigation_graph(
            investigation_id=investigation_id,
            evidence_repo=evidence_repo,
        )
    except Exception as exc:
        logger.error("get_graph_error", investigation_id=str(investigation_id), error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "GRAPH_BUILD_ERROR",
                "message": "Failed to build investigation graph.",
            },
        )


@router.post(
    "/investigations/{investigation_id}/expand",
    response_model=CytoscapeGraphResponse,
    summary="Bounded graph expansion for a known investigation address",
    description=(
        "Expand the investigation graph by fetching additional transactions from a "
        "wallet address up to a bounded depth. Expansion is strictly bounded by "
        "max_nodes, max_depth, and request_limit to prevent runaway crawling."
    ),
)
async def expand_investigation_graph(
    investigation_id: uuid.UUID,
    request: BoundedExpansionRequest,
    service: BlockchainService = Depends(get_blockchain_service),
    evidence_repo: EvidenceRepository = Depends(get_evidence_repo),
    investigation_repo: InvestigationRepository = Depends(get_investigation_repo),
) -> CytoscapeGraphResponse:
    # Verify investigation exists
    inv = await investigation_repo.get_by_id(investigation_id)
    if inv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "INVESTIGATION_NOT_FOUND",
                "message": f"Investigation '{investigation_id}' not found.",
            },
        )
    try:
        # Run bounded investigation from the address
        investigate_request = BlockchainInvestigateRequest(
            target=request.address,
            investigation_id=investigation_id,
            limit=request.request_limit,
            include_token_transfers=True,
        )
        result = await service.investigate(
            request=investigate_request,
            evidence_repo=evidence_repo,
            investigation_repo=investigation_repo,
        )
        return result.graph
    except BlockchainProviderError as exc:
        raise _handle_provider_error(exc)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "INVESTIGATION_NOT_FOUND", "message": str(exc)},
        )
    except Exception as exc:
        logger.error("expand_graph_error", investigation_id=str(investigation_id), error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "EXPANSION_ERROR",
                "message": "Graph expansion failed. Check server logs.",
            },
        )
