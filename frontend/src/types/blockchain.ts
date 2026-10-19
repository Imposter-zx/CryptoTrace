export interface NormalizedTransaction {
  tx_hash: string;
  block_number: number | null;
  block_timestamp: number | null;
  datetime_utc: string | null;
  from_address: string;
  to_address: string | null;
  value_wei: string;
  value_eth: string;
  gas_price_wei: string | null;
  gas_used: number | null;
  transaction_fee_eth: string | null;
  status: 'success' | 'failed' | 'pending' | 'unverified';
  is_error: boolean | null;
  method_id: string | null;
  function_name: string | null;
  source_provider: string;
  chain_id: number;
  retrieved_at: string;
}

export interface NormalizedTokenTransfer {
  tx_hash: string;
  block_number: number | null;
  block_timestamp: number | null;
  datetime_utc: string | null;
  from_address: string;
  to_address: string;
  token_contract_address: string;
  token_name: string | null;
  token_symbol: string | null;
  token_decimals: number | null;
  raw_amount: string;
  normalized_amount: string | null;
  event_index: number | null;
  source_provider: string;
  chain_id: number;
  retrieved_at: string;
}

export interface BlockchainResponseMeta {
  source_provider: string;
  chain_id: number;
  network: string;
  retrieved_at: string;
  item_count: number;
  is_truncated: boolean;
  warning: string | null;
}

export interface AddressTransactionsResponse {
  address: string;
  meta: BlockchainResponseMeta;
  transactions: NormalizedTransaction[];
}

export interface AddressTokenTransfersResponse {
  address: string;
  meta: BlockchainResponseMeta;
  token_transfers: NormalizedTokenTransfer[];
}

export interface TransactionDetailResponse {
  tx_hash: string;
  meta: BlockchainResponseMeta;
  transaction: NormalizedTransaction;
}

export type NodeType = 'wallet' | 'contract' | 'transaction' | 'token_contract';
export type EdgeType = 'sender_to_tx' | 'tx_to_recipient' | 'wallet_to_token_transfer' | 'contract_to_event';

export interface CytoscapeNodeData {
  id: string;
  label: string;
  node_type: NodeType;
  address: string | null;
  tx_hash: string | null;
  metadata: Record<string, unknown>;
}

export interface CytoscapeNode {
  data: CytoscapeNodeData;
}

export interface CytoscapeEdgeData {
  id: string;
  source: string;
  target: string;
  label: string;
  edge_type: EdgeType;
  value: string | null;
  symbol: string | null;
  tx_hash: string;
  evidence_id: string | null;
  metadata: Record<string, unknown>;
}

export interface CytoscapeEdge {
  data: CytoscapeEdgeData;
}

export interface GraphMeta {
  total_nodes: number;
  total_edges: number;
  is_truncated: boolean;
  max_nodes_reached: boolean;
  max_depth_reached: boolean;
  chain_id: number;
  investigation_id: string | null;
  explanation: string;
}

export interface CytoscapeGraphResponse {
  nodes: CytoscapeNode[];
  edges: CytoscapeEdge[];
  meta: GraphMeta;
}

export interface BlockchainInvestigateRequest {
  target: string;
  investigation_id?: string;
  title?: string;
  limit?: number;
  include_token_transfers?: boolean;
}

export interface BlockchainInvestigateResponse {
  investigation_id: string;
  target: string;
  target_type: 'wallet_address' | 'transaction_hash';
  evidence_created_count: number;
  evidence_skipped_duplicates_count: number;
  transactions_count: number;
  token_transfers_count: number;
  graph: CytoscapeGraphResponse;
  warnings: string[];
}

export interface BoundedExpansionRequest {
  address: string;
  max_depth?: number;
  max_nodes?: number;
  request_limit?: number;
}

export type OperationalStatus = 'ready' | 'unconfigured' | 'reachable' | 'degraded';

export interface BlockchainStatusResponse {
  provider: string;
  chain_id: number;
  network: string;
  is_configured: boolean;
  key_present: boolean;
  base_url: string;
  operational_status: OperationalStatus;
  details: Record<string, unknown> | null;
}
