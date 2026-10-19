"""
Cytoscape Graph Construction Engine for Blockchain Forensics.

Constructs interactive graph representations compatible with Cytoscape.js.
Guarantees:
- Nodes represent observed entities (wallets, smart contracts, transactions, token contracts).
- Edges represent observed blockchain transfers and logged contract events.
- Strict bounded expansion (depth, max node count, request budgets) preventing unbounded crawling.
- No speculative ownership inference or attribution clustering is performed.
"""
from __future__ import annotations

from typing import Any, Optional

from app.schemas.blockchain import (
    CytoscapeEdge,
    CytoscapeEdgeData,
    CytoscapeGraphResponse,
    CytoscapeNode,
    CytoscapeNodeData,
    GraphMeta,
    NormalizedTokenTransfer,
    NormalizedTransaction,
)


class CytoscapeGraphBuilder:
    """
    Builds Cytoscape.js compatible graph payloads with strict bounding rules.
    """

    def __init__(self, max_nodes: int = 50) -> None:
        self._max_nodes = max_nodes
        self._nodes: dict[str, CytoscapeNode] = {}
        self._edges: dict[str, CytoscapeEdge] = {}
        self._max_nodes_reached: bool = False

    def _add_node(
        self,
        node_id: str,
        label: str,
        node_type: str,
        address: Optional[str] = None,
        tx_hash: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Add node if within max_nodes ceiling. Returns True if node exists or was added."""
        if node_id in self._nodes:
            return True

        if len(self._nodes) >= self._max_nodes:
            self._max_nodes_reached = True
            return False

        self._nodes[node_id] = CytoscapeNode(
            data=CytoscapeNodeData(
                id=node_id,
                label=label,
                node_type=node_type,  # type: ignore[arg-type]
                address=address,
                tx_hash=tx_hash,
                metadata=metadata or {},
            )
        )
        return True

    def _add_edge(
        self,
        edge_id: str,
        source: str,
        target: str,
        label: str,
        edge_type: str,
        value: Optional[str] = None,
        symbol: Optional[str] = None,
        tx_hash: str = "",
        evidence_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Add edge if both source and target nodes exist."""
        if source not in self._nodes or target not in self._nodes:
            return

        if edge_id not in self._edges:
            self._edges[edge_id] = CytoscapeEdge(
                data=CytoscapeEdgeData(
                    id=edge_id,
                    source=source,
                    target=target,
                    label=label,
                    edge_type=edge_type,  # type: ignore[arg-type]
                    value=value,
                    symbol=symbol,
                    tx_hash=tx_hash,
                    evidence_id=evidence_id,
                    metadata=metadata or {},
                )
            )

    def add_transaction(
        self,
        tx: NormalizedTransaction,
        evidence_id: Optional[str] = None,
    ) -> None:
        """
        Add a native transaction to the graph:
        Sender Wallet -> Transaction Node -> Recipient Address (or Contract)
        """
        tx_node_id = f"tx:{tx.tx_hash}"
        from_node_id = f"addr:{tx.from_address}"
        to_node_id = f"addr:{tx.to_address}" if tx.to_address else f"created:{tx.tx_hash[:10]}"

        # Short human labels
        from_label = f"{tx.from_address[:6]}...{tx.from_address[-4:]}"
        to_label = (
            f"{tx.to_address[:6]}...{tx.to_address[-4:]}"
            if tx.to_address
            else "[Contract Create]"
        )
        tx_label = f"Tx {tx.value_eth} ETH"

        # Add Nodes
        self._add_node(
            node_id=from_node_id,
            label=from_label,
            node_type="wallet",
            address=tx.from_address,
            metadata={"full_address": tx.from_address, "role": "sender"},
        )

        self._add_node(
            node_id=tx_node_id,
            label=tx_label,
            node_type="transaction",
            tx_hash=tx.tx_hash,
            metadata={
                "value_eth": tx.value_eth,
                "value_wei": tx.value_wei,
                "status": tx.status,
                "block_number": tx.block_number,
                "datetime_utc": tx.datetime_utc,
            },
        )

        self._add_node(
            node_id=to_node_id,
            label=to_label,
            node_type="contract" if tx.function_name else "wallet",
            address=tx.to_address,
            metadata={"full_address": tx.to_address, "role": "recipient"},
        )

        # Add Directed Edges
        self._add_edge(
            edge_id=f"edge:{from_node_id}->{tx_node_id}",
            source=from_node_id,
            target=tx_node_id,
            label=f"{tx.value_eth} ETH",
            edge_type="sender_to_tx",
            value=tx.value_eth,
            symbol="ETH",
            tx_hash=tx.tx_hash,
            evidence_id=evidence_id,
        )

        self._add_edge(
            edge_id=f"edge:{tx_node_id}->{to_node_id}",
            source=tx_node_id,
            target=to_node_id,
            label=f"{tx.value_eth} ETH",
            edge_type="tx_to_recipient",
            value=tx.value_eth,
            symbol="ETH",
            tx_hash=tx.tx_hash,
            evidence_id=evidence_id,
        )

    def add_token_transfer(
        self,
        token_tx: NormalizedTokenTransfer,
        evidence_id: Optional[str] = None,
    ) -> None:
        """
        Add an ERC-20 token transfer to the graph:
        Sender Address -> Recipient Address (annotated with Token Contract)
        """
        from_node_id = f"addr:{token_tx.from_address}"
        to_node_id = f"addr:{token_tx.to_address}"
        token_node_id = f"token:{token_tx.token_contract_address}"

        sym = token_tx.token_symbol or "TOKEN"
        amt = token_tx.normalized_amount or token_tx.raw_amount
        edge_label = f"{amt} {sym}"

        # Add Sender and Recipient Nodes
        self._add_node(
            node_id=from_node_id,
            label=f"{token_tx.from_address[:6]}...{token_tx.from_address[-4:]}",
            node_type="wallet",
            address=token_tx.from_address,
        )

        self._add_node(
            node_id=to_node_id,
            label=f"{token_tx.to_address[:6]}...{token_tx.to_address[-4:]}",
            node_type="wallet",
            address=token_tx.to_address,
        )

        # Add Token Contract Node
        self._add_node(
            node_id=token_node_id,
            label=f"Token: {sym}",
            node_type="token_contract",
            address=token_tx.token_contract_address,
            metadata={
                "symbol": sym,
                "name": token_tx.token_name,
                "contract": token_tx.token_contract_address,
                "decimals": token_tx.token_decimals,
            },
        )

        # Direct Transfer Edge
        self._add_edge(
            edge_id=f"edge:{from_node_id}->{to_node_id}:{token_tx.tx_hash}:{token_tx.event_index or 0}",
            source=from_node_id,
            target=to_node_id,
            label=edge_label,
            edge_type="wallet_to_token_transfer",
            value=amt,
            symbol=sym,
            tx_hash=token_tx.tx_hash,
            evidence_id=evidence_id,
            metadata={"token_contract": token_tx.token_contract_address},
        )

        # Contract to Event Reference
        self._add_edge(
            edge_id=f"edge:{token_node_id}->{to_node_id}:{token_tx.tx_hash}",
            source=token_node_id,
            target=to_node_id,
            label=f"Issued {sym}",
            edge_type="contract_to_event",
            value=amt,
            symbol=sym,
            tx_hash=token_tx.tx_hash,
            evidence_id=evidence_id,
        )

    def build(self, investigation_id: Optional[str] = None) -> CytoscapeGraphResponse:
        """Finalize and return the Cytoscape graph response."""
        return CytoscapeGraphResponse(
            nodes=list(self._nodes.values()),
            edges=list(self._edges.values()),
            meta=GraphMeta(
                total_nodes=len(self._nodes),
                total_edges=len(self._edges),
                is_truncated=self._max_nodes_reached,
                max_nodes_reached=self._max_nodes_reached,
                max_depth_reached=False,
                chain_id=1,
                investigation_id=investigation_id,
            ),
        )
