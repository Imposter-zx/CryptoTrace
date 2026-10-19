"""
Blockchain Investigation Service — Phase 2 coordination layer.

Responsibilities:
- Delegates all provider calls to a BlockchainAdapter (currently EtherscanAdapter).
- Normalizes raw provider data into canonical schemas.
- Stores evidence idempotently in the database via EvidenceRepository.
- Builds Cytoscape.js graph from evidence-backed normalized transactions.
- Enforces all security and precision constraints (no float arithmetic, no secret leakage).

Architecture:
- This service never calls the database directly — all DB access goes through repositories.
- Provider-specific logic stays inside adapters; normalization is service-layer responsibility.
- All cryptocurrency amounts are computed using Python Decimal, never float.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

import structlog

from app.adapters.blockchain.base import BlockchainAdapter
from app.adapters.blockchain.etherscan import (
    BlockchainProviderError,
    BlockchainResourceNotFoundError,
    EtherscanAdapter,
)
from app.core.config import settings
from app.db.repositories.evidence import EvidenceRepository
from app.db.repositories.investigations import InvestigationRepository
from app.engine.graph_builder import CytoscapeGraphBuilder
from app.models.investigations import (
    EvidenceAssessment,
    EvidenceType,
    InvestigationStatus,
)
from app.schemas.blockchain import (
    AddressTokenTransfersResponse,
    AddressTransactionsResponse,
    BlockchainInvestigateRequest,
    BlockchainInvestigateResponse,
    BlockchainResponseMeta,
    BlockchainStatusResponse,
    BoundedExpansionRequest,
    CytoscapeGraphResponse,
    NormalizedTokenTransfer,
    NormalizedTransaction,
    TransactionDetailResponse,
)
from app.schemas.investigations import InvestigationCreate
from app.utils.ethereum import (
    canonical_json_dumps,
    compute_integrity_hash,
    is_valid_ethereum_address,
    raw_to_token_amount,
    validate_and_normalize_address,
    wei_to_ether,
)

logger = structlog.get_logger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

_ETHERSCAN_ADAPTER_KEY = "etherscan_v2"
_DEFAULT_MAX_NODES = 50


# ── Normalization helpers ──────────────────────────────────────────────────────

def _safe_int(value: object, default: Optional[int] = None) -> Optional[int]:
    """Safely parse an int from a string/int without raising."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _normalize_transaction(raw: dict, retrieved_at: str) -> NormalizedTransaction:
    """
    Convert a raw Etherscan txlist record into a NormalizedTransaction.

    Precision guarantees:
    - Wei values are kept as strings (never converted to float).
    - ETH values use exact Python Decimal arithmetic.
    - Timestamps are converted to ISO-8601 strings.
    """
    from_addr = raw.get("from", "") or ""
    to_addr = raw.get("to", "") or None

    # Address normalization: validate but be tolerant of minor case variations
    try:
        from_addr = validate_and_normalize_address(from_addr) if from_addr else from_addr
    except ValueError:
        pass  # keep raw; log below

    if to_addr:
        try:
            to_addr = validate_and_normalize_address(to_addr)
        except ValueError:
            pass  # keep raw

    value_wei_str = str(raw.get("value", "0") or "0")
    value_eth = str(wei_to_ether(value_wei_str))

    gas_price_str: Optional[str] = str(raw.get("gasPrice", "") or "") or None
    gas_used = _safe_int(raw.get("gasUsed"))
    tx_fee_eth: Optional[str] = None
    if gas_price_str and gas_used is not None:
        try:
            fee_wei = int(gas_price_str) * gas_used
            tx_fee_eth = str(wei_to_ether(str(fee_wei)))
        except (ValueError, TypeError):
            pass

    block_ts = _safe_int(raw.get("timeStamp"))
    datetime_utc: Optional[str] = None
    if block_ts is not None:
        try:
            datetime_utc = datetime.fromtimestamp(block_ts, tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            pass

    is_error_raw = raw.get("isError")
    is_error: Optional[bool] = None
    if is_error_raw is not None:
        try:
            is_error = bool(int(is_error_raw))
        except (ValueError, TypeError):
            pass

    if is_error is True:
        tx_status = "failed"
    elif raw.get("txreceipt_status") == "1":
        tx_status = "success"
    else:
        tx_status = "unverified"

    input_data: str = str(raw.get("input", "") or "")
    method_id = input_data[:10] if len(input_data) >= 10 and input_data.startswith("0x") else None

    tx_hash = str(raw.get("hash", raw.get("txhash", ""))).lower()

    return NormalizedTransaction(
        tx_hash=tx_hash,
        block_number=_safe_int(raw.get("blockNumber")),
        block_timestamp=block_ts,
        datetime_utc=datetime_utc,
        from_address=from_addr,
        to_address=to_addr,
        value_wei=value_wei_str,
        value_eth=value_eth,
        gas_price_wei=gas_price_str,
        gas_used=gas_used,
        transaction_fee_eth=tx_fee_eth,
        status=tx_status,
        is_error=is_error,
        method_id=method_id,
        function_name=raw.get("functionName") or None,
        source_provider=_ETHERSCAN_ADAPTER_KEY,
        chain_id=settings.ETHERSCAN_CHAIN_ID,
        retrieved_at=retrieved_at,
    )


def _normalize_proxy_transaction(raw: dict, retrieved_at: str) -> NormalizedTransaction:
    """
    Convert a raw Etherscan proxy (eth_getTransactionByHash) response.

    The proxy module returns hex-encoded values; account module uses decimal strings.
    """
    from_addr = raw.get("from", "") or ""
    to_addr = raw.get("to") or None

    try:
        from_addr = validate_and_normalize_address(from_addr) if from_addr else from_addr
    except ValueError:
        pass

    if to_addr:
        try:
            to_addr = validate_and_normalize_address(to_addr)
        except ValueError:
            pass

    # Proxy returns hex strings: "0x..."
    value_hex = str(raw.get("value", "0x0") or "0x0")
    try:
        value_wei_int = int(value_hex, 16)
    except ValueError:
        value_wei_int = 0
    value_wei_str = str(value_wei_int)
    value_eth = str(wei_to_ether(value_wei_str))

    gas_price_hex = raw.get("gasPrice") or None
    gas_price_str: Optional[str] = None
    if gas_price_hex:
        try:
            gas_price_str = str(int(gas_price_hex, 16))
        except ValueError:
            pass

    block_number_hex = raw.get("blockNumber")
    block_number: Optional[int] = None
    if block_number_hex:
        try:
            block_number = int(block_number_hex, 16)
        except ValueError:
            pass

    tx_hash = str(raw.get("hash", "")).lower()

    return NormalizedTransaction(
        tx_hash=tx_hash,
        block_number=block_number,
        block_timestamp=None,
        datetime_utc=None,
        from_address=from_addr,
        to_address=to_addr,
        value_wei=value_wei_str,
        value_eth=value_eth,
        gas_price_wei=gas_price_str,
        gas_used=None,
        transaction_fee_eth=None,
        status="unverified",
        is_error=None,
        method_id=None,
        function_name=None,
        source_provider=_ETHERSCAN_ADAPTER_KEY,
        chain_id=settings.ETHERSCAN_CHAIN_ID,
        retrieved_at=retrieved_at,
    )


def _normalize_token_transfer(raw: dict, retrieved_at: str) -> NormalizedTokenTransfer:
    """
    Convert a raw Etherscan tokentx record into NormalizedTokenTransfer.

    Precision guarantees:
    - raw_amount is kept as the exact integer string.
    - normalized_amount is computed via Decimal arithmetic using actual decimals.
    - If token_decimals is None or missing, normalized_amount is set to None.
    - We NEVER assume 18 decimals.
    """
    from_addr = raw.get("from", "") or ""
    to_addr = raw.get("to", "") or ""
    token_addr = raw.get("contractAddress", "") or ""

    for addr_var, addr_val in [("from", from_addr), ("to", to_addr), ("contract", token_addr)]:
        try:
            if addr_var == "from":
                from_addr = validate_and_normalize_address(addr_val) if addr_val else addr_val
            elif addr_var == "to":
                to_addr = validate_and_normalize_address(addr_val) if addr_val else addr_val
            else:
                token_addr = validate_and_normalize_address(addr_val) if addr_val else addr_val
        except ValueError:
            pass  # keep raw value

    raw_amount_str = str(raw.get("value", "0") or "0")

    decimals_raw = raw.get("tokenDecimal")
    token_decimals: Optional[int] = None
    if decimals_raw is not None and str(decimals_raw).strip() != "":
        token_decimals = _safe_int(decimals_raw)

    normalized_amount: Optional[str] = None
    if token_decimals is not None:
        amt = raw_to_token_amount(raw_amount_str, token_decimals)
        if amt is not None:
            normalized_amount = str(amt)

    block_ts = _safe_int(raw.get("timeStamp"))
    datetime_utc: Optional[str] = None
    if block_ts is not None:
        try:
            datetime_utc = datetime.fromtimestamp(block_ts, tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            pass

    tx_hash = str(raw.get("hash", raw.get("txhash", ""))).lower()

    return NormalizedTokenTransfer(
        tx_hash=tx_hash,
        block_number=_safe_int(raw.get("blockNumber")),
        block_timestamp=block_ts,
        datetime_utc=datetime_utc,
        from_address=from_addr,
        to_address=to_addr,
        token_contract_address=token_addr,
        token_name=raw.get("tokenName") or None,
        token_symbol=raw.get("tokenSymbol") or None,
        token_decimals=token_decimals,
        raw_amount=raw_amount_str,
        normalized_amount=normalized_amount,
        event_index=_safe_int(raw.get("transactionIndex")),
        source_provider=_ETHERSCAN_ADAPTER_KEY,
        chain_id=settings.ETHERSCAN_CHAIN_ID,
        retrieved_at=retrieved_at,
    )


def _make_response_meta(
    item_count: int,
    limit: int,
) -> BlockchainResponseMeta:
    return BlockchainResponseMeta(
        source_provider=_ETHERSCAN_ADAPTER_KEY,
        chain_id=settings.ETHERSCAN_CHAIN_ID,
        network="ethereum_mainnet",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
        item_count=item_count,
        is_truncated=item_count >= limit,
        warning=("Result may be truncated — provider limit reached." if item_count >= limit else None),
    )


# ── Service ────────────────────────────────────────────────────────────────────

class BlockchainService:
    """
    Coordinates blockchain data retrieval, normalization, evidence storage,
    and graph construction.

    Designed for dependency injection in FastAPI endpoints; takes a DB session
    and optional custom adapter for testing.
    """

    def __init__(
        self,
        adapter: Optional[BlockchainAdapter] = None,
    ) -> None:
        self._adapter: BlockchainAdapter = adapter or EtherscanAdapter()

    # ── Status ─────────────────────────────────────────────────────────────────

    async def get_status(self) -> BlockchainStatusResponse:
        """Probe provider connectivity. Never exposes API key or secrets."""
        info = await self._adapter.check_connectivity()
        return BlockchainStatusResponse(
            provider=info.get("provider", self._adapter.provider_name),
            chain_id=info.get("chain_id", self._adapter.chain_id),
            network=info.get("network", "ethereum_mainnet"),
            is_configured=info.get("is_configured", False),
            key_present=info.get("key_present", False),
            base_url=info.get("base_url", ""),
            operational_status=info.get("operational_status", "unconfigured"),
            details=info.get("details"),
        )

    # ── Transaction ────────────────────────────────────────────────────────────

    async def get_transaction(self, tx_hash: str) -> TransactionDetailResponse:
        """Retrieve and normalize a single transaction by hash."""
        retrieved_at = datetime.now(timezone.utc).isoformat()
        raw = await self._adapter.get_transaction(tx_hash)
        normalized = _normalize_proxy_transaction(raw, retrieved_at)
        return TransactionDetailResponse(
            tx_hash=tx_hash,
            meta=_make_response_meta(1, 1),
            transaction=normalized,
        )

    # ── Address data ───────────────────────────────────────────────────────────

    async def get_address_transactions(
        self,
        address: str,
        limit: int = 25,
        offset: int = 0,
    ) -> AddressTransactionsResponse:
        """Retrieve and normalize native transactions for a wallet."""
        retrieved_at = datetime.now(timezone.utc).isoformat()
        raw_list = await self._adapter.get_address_transactions(
            address, limit=limit, offset=offset
        )
        normalized = [_normalize_transaction(r, retrieved_at) for r in raw_list]
        return AddressTransactionsResponse(
            address=address,
            meta=_make_response_meta(len(normalized), limit),
            transactions=normalized,
        )

    async def get_address_token_transfers(
        self,
        address: str,
        limit: int = 25,
        offset: int = 0,
    ) -> AddressTokenTransfersResponse:
        """Retrieve and normalize ERC-20 token transfers for a wallet."""
        retrieved_at = datetime.now(timezone.utc).isoformat()
        raw_list = await self._adapter.get_address_token_transfers(
            address, limit=limit, offset=offset
        )
        normalized = [_normalize_token_transfer(r, retrieved_at) for r in raw_list]
        return AddressTokenTransfersResponse(
            address=address,
            meta=_make_response_meta(len(normalized), limit),
            token_transfers=normalized,
        )

    # ── Core investigation workflow ────────────────────────────────────────────

    async def investigate(
        self,
        request: BlockchainInvestigateRequest,
        evidence_repo: EvidenceRepository,
        investigation_repo: InvestigationRepository,
    ) -> BlockchainInvestigateResponse:
        """
        Full blockchain investigation workflow:

        1. Determine target type (address vs tx hash).
        2. Create or reuse an Investigation record.
        3. Fetch raw data from the blockchain provider.
        4. Normalize each result.
        5. Compute SHA-256 integrity hash (scope: canonical JSON of raw payload).
        6. Upsert evidence idempotently — NEVER overwrite existing raw_data.
        7. Build Cytoscape.js graph with evidence-backed edges.
        8. Return complete response.
        """
        target = request.target
        target_type: str
        warnings: list[str] = []
        retrieved_at = datetime.now(timezone.utc).isoformat()

        is_address = is_valid_ethereum_address(target)
        if is_address:
            target_type = "wallet_address"
        else:
            target_type = "transaction_hash"

        # ── 1. Get or create investigation ─────────────────────────────────────
        investigation_id: uuid.UUID
        if request.investigation_id is not None:
            # Verify investigation exists
            inv = await investigation_repo.get_by_id(request.investigation_id)
            if inv is None:
                raise ValueError(
                    f"Investigation '{request.investigation_id}' not found or is archived."
                )
            investigation_id = inv.id
        else:
            title = request.title or (
                f"ETH {'Wallet' if is_address else 'Transaction'} Investigation: "
                f"{target[:12]}...{target[-6:]}"
            )
            inv = await investigation_repo.create(
                InvestigationCreate(
                    title=title,
                    description=(
                        f"Auto-created by blockchain investigation of {target_type} {target}."
                    ),
                    status=InvestigationStatus.ACTIVE,
                )
            )
            investigation_id = inv.id

        # ── 2. Fetch evidence source ────────────────────────────────────────────
        source = await evidence_repo.get_source_by_adapter_key(_ETHERSCAN_ADAPTER_KEY)
        source_id: Optional[uuid.UUID] = source.id if source else None
        if source is None:
            warnings.append(
                "EvidenceSource for 'etherscan_v2' not found in database. "
                "Evidence provenance chain is incomplete. Run 'alembic upgrade head'."
            )

        # ── 3. Retrieve data from provider ─────────────────────────────────────
        raw_transactions: list[dict] = []
        raw_token_transfers: list[dict] = []

        if target_type == "wallet_address":
            try:
                raw_transactions = await self._adapter.get_address_transactions(
                    target, limit=request.limit
                )
            except BlockchainProviderError as exc:
                warnings.append(f"Transaction retrieval error: {exc}")

            if request.include_token_transfers:
                try:
                    raw_token_transfers = await self._adapter.get_address_token_transfers(
                        target, limit=request.limit
                    )
                except BlockchainProviderError as exc:
                    warnings.append(f"Token transfer retrieval error: {exc}")

        else:
            # tx_hash investigation — fetch single transaction
            try:
                raw_tx = await self._adapter.get_transaction(target)
                raw_transactions = [raw_tx]
            except BlockchainResourceNotFoundError as exc:
                warnings.append(f"Transaction not found: {exc}")
            except BlockchainProviderError as exc:
                warnings.append(f"Transaction retrieval error: {exc}")

        # ── 4. Normalize ────────────────────────────────────────────────────────
        normalized_txs: list[NormalizedTransaction] = []
        for raw in raw_transactions:
            try:
                if target_type == "transaction_hash":
                    normalized_txs.append(_normalize_proxy_transaction(raw, retrieved_at))
                else:
                    normalized_txs.append(_normalize_transaction(raw, retrieved_at))
            except Exception as exc:
                logger.warning("tx_normalization_failed", error=str(exc))
                warnings.append(f"Skipped malformed transaction record: {exc}")

        normalized_transfers: list[NormalizedTokenTransfer] = []
        for raw in raw_token_transfers:
            try:
                normalized_transfers.append(_normalize_token_transfer(raw, retrieved_at))
            except Exception as exc:
                logger.warning("token_transfer_normalization_failed", error=str(exc))
                warnings.append(f"Skipped malformed token transfer record: {exc}")

        # ── 5. Persist evidence idempotently ────────────────────────────────────
        graph = CytoscapeGraphBuilder(max_nodes=_DEFAULT_MAX_NODES)
        evidence_created = 0
        evidence_skipped = 0

        for ntx in normalized_txs:
            canonical = canonical_json_dumps({
                "provider": _ETHERSCAN_ADAPTER_KEY,
                "endpoint": "txlist" if target_type == "wallet_address" else "eth_getTransactionByHash",
                "chain_id": settings.ETHERSCAN_CHAIN_ID,
                "timestamp": retrieved_at,
                "result": ntx.model_dump(mode="json"),
            })
            integrity_hash = compute_integrity_hash({"_raw": canonical})

            ev, created = await evidence_repo.get_or_create_evidence(
                investigation_id=investigation_id,
                evidence_type=EvidenceType.BLOCKCHAIN_TRANSACTION,
                title=f"ETH Tx {ntx.tx_hash[:18]}...",
                external_reference=ntx.tx_hash,
                raw_data={"raw_response": raw_transactions[normalized_txs.index(ntx)] if target_type != "transaction_hash" else None, "normalized": ntx.model_dump(mode="json")},
                normalized_data=ntx.model_dump(mode="json"),
                integrity_hash=integrity_hash,
                assessment=EvidenceAssessment.PROVIDER_SUPPLIED,
                assessment_rationale=(
                    "Data retrieved directly from Etherscan V2 API. "
                    "Integrity hash detects modification of stored payload only; "
                    "does not independently verify provider veracity."
                ),
                source_id=source_id,
                collected_at=datetime.now(timezone.utc),
            )

            if created:
                evidence_created += 1
            else:
                evidence_skipped += 1

            graph.add_transaction(ntx, evidence_id=str(ev.id))

        for ntt in normalized_transfers:
            canonical = canonical_json_dumps({
                "provider": _ETHERSCAN_ADAPTER_KEY,
                "endpoint": "tokentx",
                "chain_id": settings.ETHERSCAN_CHAIN_ID,
                "timestamp": retrieved_at,
                "result": ntt.model_dump(mode="json"),
            })
            integrity_hash = compute_integrity_hash({"_raw": canonical})

            ev_key = f"{ntt.tx_hash}:{ntt.token_contract_address}:{ntt.event_index or 0}"
            ev, created = await evidence_repo.get_or_create_evidence(
                investigation_id=investigation_id,
                evidence_type=EvidenceType.BLOCKCHAIN_TRANSACTION,
                title=f"ERC-20 Transfer {ntt.token_symbol or 'TOKEN'} in {ntt.tx_hash[:18]}...",
                external_reference=ev_key,
                raw_data={"normalized": ntt.model_dump(mode="json")},
                normalized_data=ntt.model_dump(mode="json"),
                integrity_hash=integrity_hash,
                assessment=EvidenceAssessment.PROVIDER_SUPPLIED,
                assessment_rationale=(
                    "ERC-20 transfer event retrieved from Etherscan V2 tokentx endpoint. "
                    "Token decimals preserved exactly; normalized_amount is None when decimals unknown."
                ),
                source_id=source_id,
                collected_at=datetime.now(timezone.utc),
            )

            if created:
                evidence_created += 1
            else:
                evidence_skipped += 1

            graph.add_token_transfer(ntt, evidence_id=str(ev.id))

        cytoscape_graph = graph.build(investigation_id=str(investigation_id))

        if cytoscape_graph.meta.max_nodes_reached:
            warnings.append(
                f"Graph node ceiling ({_DEFAULT_MAX_NODES}) reached. "
                "Some nodes and edges were omitted from the visualization."
            )

        return BlockchainInvestigateResponse(
            investigation_id=investigation_id,
            target=target,
            target_type=target_type,  # type: ignore[arg-type]
            evidence_created_count=evidence_created,
            evidence_skipped_duplicates_count=evidence_skipped,
            transactions_count=len(normalized_txs),
            token_transfers_count=len(normalized_transfers),
            graph=cytoscape_graph,
            warnings=warnings,
        )

    async def get_investigation_graph(
        self,
        investigation_id: uuid.UUID,
        evidence_repo: EvidenceRepository,
    ) -> CytoscapeGraphResponse:
        """
        Rebuild the Cytoscape.js graph from persisted evidence records.
        Does not re-query the blockchain provider.
        """
        evidence_list = await evidence_repo.get_evidence_for_investigation(
            investigation_id,
            evidence_type=EvidenceType.BLOCKCHAIN_TRANSACTION,
        )

        graph = CytoscapeGraphBuilder(max_nodes=_DEFAULT_MAX_NODES)
        retrieved_at = datetime.now(timezone.utc).isoformat()

        for ev in evidence_list:
            if ev.normalized_data is None:
                continue
            nd = ev.normalized_data
            # Reconstruct from normalized_data JSON
            if "tx_hash" in nd and "value_wei" in nd:
                # Native transaction
                try:
                    ntx = NormalizedTransaction(**nd)
                    graph.add_transaction(ntx, evidence_id=str(ev.id))
                except Exception as exc:
                    logger.warning("graph_rebuild_tx_skip", evidence_id=str(ev.id), error=str(exc))
            elif "tx_hash" in nd and "token_contract_address" in nd:
                # Token transfer
                try:
                    ntt = NormalizedTokenTransfer(**nd)
                    graph.add_token_transfer(ntt, evidence_id=str(ev.id))
                except Exception as exc:
                    logger.warning("graph_rebuild_token_skip", evidence_id=str(ev.id), error=str(exc))

        return graph.build(investigation_id=str(investigation_id))
