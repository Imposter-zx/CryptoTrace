"""
Pydantic schemas for Blockchain Forensics, Data Normalization, and Cytoscape Graph Construction.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.ethereum import (
    is_valid_ethereum_address,
    is_valid_tx_hash,
    validate_and_normalize_address,
    validate_and_normalize_tx_hash,
)


class BaseBlockchainSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ── Normalized Entities ───────────────────────────────────────────────────────

class NormalizedTransaction(BaseBlockchainSchema):
    """
    Standardized Ethereum Native Transaction.
    Preserves exact raw quantities alongside exact decimal human-readable values.
    """
    tx_hash: str = Field(..., description="0x-prefixed 32-byte transaction hash")
    block_number: Optional[int] = Field(None, description="Block height number")
    block_timestamp: Optional[int] = Field(None, description="Block timestamp in Unix seconds")
    datetime_utc: Optional[str] = Field(None, description="ISO-8601 formatted UTC timestamp")
    from_address: str = Field(..., description="Checksummed sender address")
    to_address: Optional[str] = Field(None, description="Checksummed recipient address or None for creation")
    value_wei: str = Field(..., description="Exact native value in wei (raw integer string)")
    value_eth: str = Field(..., description="Exact native value in Ether (decimal arithmetic string)")
    gas_price_wei: Optional[str] = Field(None, description="Gas price in wei")
    gas_used: Optional[int] = Field(None, description="Gas units consumed by execution")
    transaction_fee_eth: Optional[str] = Field(
        None, description="Exact transaction fee in Ether (gas_price * gas_used)"
    )
    status: str = Field(
        default="unverified",
        description="Transaction status: 'success', 'failed', 'pending', or 'unverified'",
    )
    is_error: Optional[bool] = Field(None, description="True if transaction reverted")
    method_id: Optional[str] = Field(None, description="First 4 bytes of input data (0x...)")
    function_name: Optional[str] = Field(None, description="Contract method name if available")
    source_provider: str = Field(..., description="Source provider identifier (e.g., 'etherscan_v2')")
    chain_id: int = Field(default=1, description="EIP-155 Chain ID (1 for Ethereum Mainnet)")
    retrieved_at: str = Field(..., description="ISO-8601 UTC retrieval timestamp")


class NormalizedTokenTransfer(BaseBlockchainSchema):
    """
    Standardized ERC-20 Token Transfer Event.
    Strictly segregated from native ETH transactions.
    """
    tx_hash: str = Field(..., description="0x-prefixed 32-byte transaction hash")
    block_number: Optional[int] = Field(None, description="Block height number")
    block_timestamp: Optional[int] = Field(None, description="Block timestamp in Unix seconds")
    datetime_utc: Optional[str] = Field(None, description="ISO-8601 formatted UTC timestamp")
    from_address: str = Field(..., description="Checksummed sender address")
    to_address: str = Field(..., description="Checksummed recipient address")
    token_contract_address: str = Field(..., description="Checksummed ERC-20 contract address")
    token_name: Optional[str] = Field(None, description="Token name if provided by contract/provider")
    token_symbol: Optional[str] = Field(None, description="Token ticker symbol (e.g. USDT, DAI)")
    token_decimals: Optional[int] = Field(
        None, description="Token decimal places. Preserved exactly; None if unknown."
    )
    raw_amount: str = Field(..., description="Raw integer token amount in smallest unit")
    normalized_amount: Optional[str] = Field(
        None,
        description="Normalized human-readable token amount using actual decimals. None if decimals unknown.",
    )
    event_index: Optional[int] = Field(None, description="Log event index within the block/tx")
    source_provider: str = Field(..., description="Source provider identifier")
    chain_id: int = Field(default=1, description="EIP-155 Chain ID")
    retrieved_at: str = Field(..., description="ISO-8601 UTC retrieval timestamp")


# ── Provenance & Integrity Wrappers ───────────────────────────────────────────

class ProvenanceMetadata(BaseBlockchainSchema):
    provider_id: str
    endpoint: str
    chain_id: int
    network: str = "ethereum_mainnet"
    retrieval_timestamp: str
    target_reference: str
    integrity_hash: str
    integrity_scope_notice: str = (
        "SHA-256 hash detects modification or corruption of the stored canonical JSON "
        "representation. It does not independently verify external provider veracity."
    )


class BlockchainResponseMeta(BaseBlockchainSchema):
    source_provider: str
    chain_id: int
    network: str = "ethereum_mainnet"
    retrieved_at: str
    item_count: int
    is_truncated: bool = False
    warning: Optional[str] = None


class AddressTransactionsResponse(BaseBlockchainSchema):
    address: str
    meta: BlockchainResponseMeta
    transactions: list[NormalizedTransaction]


class AddressTokenTransfersResponse(BaseBlockchainSchema):
    address: str
    meta: BlockchainResponseMeta
    token_transfers: list[NormalizedTokenTransfer]


class TransactionDetailResponse(BaseBlockchainSchema):
    tx_hash: str
    meta: BlockchainResponseMeta
    transaction: NormalizedTransaction


# ── Graph Construction (Cytoscape.js Compatible) ──────────────────────────────

NodeType = Literal["wallet", "contract", "transaction", "token_contract"]
EdgeType = Literal[
    "sender_to_tx",
    "tx_to_recipient",
    "wallet_to_token_transfer",
    "contract_to_event",
]


class CytoscapeNodeData(BaseBlockchainSchema):
    id: str
    label: str
    node_type: NodeType
    address: Optional[str] = None
    tx_hash: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CytoscapeNode(BaseBlockchainSchema):
    data: CytoscapeNodeData


class CytoscapeEdgeData(BaseBlockchainSchema):
    id: str
    source: str
    target: str
    label: str
    edge_type: EdgeType
    value: Optional[str] = None
    symbol: Optional[str] = None
    tx_hash: str
    evidence_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CytoscapeEdge(BaseBlockchainSchema):
    data: CytoscapeEdgeData


class GraphMeta(BaseBlockchainSchema):
    total_nodes: int
    total_edges: int
    is_truncated: bool = False
    max_nodes_reached: bool = False
    max_depth_reached: bool = False
    chain_id: int = 1
    investigation_id: Optional[str] = None
    explanation: str = (
        "Graph edges strictly represent observed blockchain transactions and logged token events. "
        "No common wallet ownership or coordinated attribution is inferred."
    )


class CytoscapeGraphResponse(BaseBlockchainSchema):
    nodes: list[CytoscapeNode]
    edges: list[CytoscapeEdge]
    meta: GraphMeta


# ── Investigation Intake & Expansion ──────────────────────────────────────────

class BlockchainInvestigateRequest(BaseBlockchainSchema):
    target: str = Field(..., description="Ethereum wallet address (0x...) or transaction hash (0x...)")
    investigation_id: Optional[uuid.UUID] = Field(
        None, description="Optional existing investigation ID to attach evidence to"
    )
    title: Optional[str] = Field(None, max_length=255, description="Custom case title if creating new")
    limit: int = Field(default=25, ge=1, le=100, description="Max transactions to retrieve")
    include_token_transfers: bool = Field(default=True, description="Whether to include ERC-20 transfers")

    @field_validator("target")
    @classmethod
    def validate_target(cls, v: str) -> str:
        trimmed = v.strip()
        if is_valid_ethereum_address(trimmed):
            return validate_and_normalize_address(trimmed)
        if is_valid_tx_hash(trimmed):
            return validate_and_normalize_tx_hash(trimmed)
        raise ValueError(
            f"Invalid target '{v}'. Target must be a valid 20-byte Ethereum address (0x...) "
            "or 32-byte transaction hash (0x... 64 hex characters)."
        )


class BlockchainInvestigateResponse(BaseBlockchainSchema):
    investigation_id: uuid.UUID
    target: str
    target_type: Literal["wallet_address", "transaction_hash"]
    evidence_created_count: int
    evidence_skipped_duplicates_count: int
    transactions_count: int
    token_transfers_count: int
    graph: CytoscapeGraphResponse
    warnings: list[str] = Field(default_factory=list)


class BoundedExpansionRequest(BaseBlockchainSchema):
    address: str = Field(..., description="Ethereum wallet address to expand from")
    max_depth: int = Field(default=1, ge=1, le=2, description="Bounded expansion depth")
    max_nodes: int = Field(default=30, ge=5, le=100, description="Max total graph nodes ceiling")
    request_limit: int = Field(default=10, ge=1, le=25, description="Max records to retrieve per hop")

    @field_validator("address")
    @classmethod
    def validate_address_field(cls, v: str) -> str:
        return validate_and_normalize_address(v.strip())


# ── Provider Operational Status ───────────────────────────────────────────────

class BlockchainStatusResponse(BaseBlockchainSchema):
    provider: str
    chain_id: int
    network: str
    is_configured: bool
    key_present: bool
    base_url: str
    operational_status: Literal["ready", "unconfigured", "reachable", "degraded"]
    details: Optional[dict[str, Any]] = None
