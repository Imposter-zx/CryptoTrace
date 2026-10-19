# CryptoTrace AI — REST API Documentation (v1)

Base URL: `http://localhost:8000/api/v1`
Interactive OpenAPI Documentation: `http://localhost:8000/docs`
ReDoc Reference: `http://localhost:8000/redoc`

---

## 1. Health & Readiness

### `GET /health`
Liveness check for container orchestration and process supervision.

- **Response `200 OK`**:
```json
{
  "status": "ok",
  "service": "CryptoTrace AI"
}
```

### `GET /api/v1/health`
Deep readiness check verifying active database pool connectivity.

- **Response `200 OK` (Healthy)**:
```json
{
  "status": "ok",
  "service": "CryptoTrace AI",
  "version": "0.1.0",
  "database": "ok",
  "details": {
    "database": {
      "version": "PostgreSQL 16.2 on x86_64-pc-linux-gnu..."
    }
  }
}
```

- **Response `200 OK` (Degraded)**:
```json
{
  "status": "degraded",
  "service": "CryptoTrace AI",
  "version": "0.1.0",
  "database": "unavailable",
  "details": {
    "database": {
      "error": "Database connection failed. Check DATABASE_URL."
    }
  }
}
```

---

## 2. Investigations API

### `POST /api/v1/investigations`
Create a new forensic investigation case.

- **Request Body**:
```json
{
  "title": "Ransomware Payment Trace — Operation BlackShield",
  "description": "Tracing 14.5 BTC illicit ransom payout across hop addresses.",
  "status": "active",
  "priority": "high",
  "tags": ["ransomware", "bitcoin", "darknet"],
  "case_reference": "CASE-2026-089"
}
```

- **Validation Rules**:
  - `title`: String between 1 and 255 chars, non-empty, auto-trimmed.
  - `description`: Optional text up to 10,000 characters.
  - `status`: Enum `draft | active | on_hold | closed | archived` (default: `draft`).
  - `priority`: Enum `low | medium | high | critical` (default: `medium`).
  - `tags`: Array of up to 50 trimmed string tags.
  - `case_reference`: Optional reference code up to 100 chars.

- **Response `201 Created`**:
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "title": "Ransomware Payment Trace — Operation BlackShield",
  "description": "Tracing 14.5 BTC illicit ransom payout across hop addresses.",
  "status": "active",
  "priority": "high",
  "tags": ["ransomware", "bitcoin", "darknet"],
  "case_reference": "CASE-2026-089",
  "is_archived": false,
  "closed_at": null,
  "created_at": "2026-10-15T00:50:00Z",
  "updated_at": "2026-10-15T00:50:00Z",
  "evidence_count": 0
}
```

---

### `GET /api/v1/investigations`
List forensic investigations with server-side pagination, status filtering, and multi-field text search.

- **Query Parameters**:
  - `page` (integer, default `1`, min `1`)
  - `page_size` (integer, default `20`, min `1`, max `100`)
  - `status` (optional enum: `draft`, `active`, `on_hold`, `closed`, `archived`)
  - `search` (optional string, searches `title`, `description`, and `case_reference`)

- **Response `200 OK`**:
```json
{
  "items": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "title": "Ransomware Payment Trace — Operation BlackShield",
      "description": "Tracing 14.5 BTC illicit ransom payout across hop addresses.",
      "status": "active",
      "priority": "high",
      "tags": ["ransomware", "bitcoin"],
      "case_reference": "CASE-2026-089",
      "is_archived": false,
      "closed_at": null,
      "created_at": "2026-10-15T00:50:00Z",
      "updated_at": "2026-10-15T00:50:00Z",
      "evidence_count": 0
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

---

### `GET /api/v1/investigations/summary`
Retrieve real-time aggregate counts partitioned by investigation status.

- **Response `200 OK`**:
```json
{
  "status_counts": {
    "draft": 2,
    "active": 5,
    "on_hold": 1,
    "closed": 4
  }
}
```

---

### `GET /api/v1/investigations/{id}`
Retrieve a single investigation record by its UUID.

- **Response `200 OK`**: returns `InvestigationResponse` object.
- **Response `404 Not Found`**:
```json
{
  "detail": "Investigation with ID 3fa85f64-5717-4562-b3fc-2c963f66afa6 not found.",
  "error_code": "NOT_FOUND"
}
```

---

### `PATCH /api/v1/investigations/{id}`
Partially update investigation metadata.

- **Request Body**: any subset of `title`, `description`, `status`, `priority`, `tags`, `case_reference`.
- **Response `200 OK`**: returns updated `InvestigationResponse`.

---

### `DELETE /api/v1/investigations/{id}`
Safely archives (soft-deletes) an investigation while maintaining database integrity.

- **Response `200 OK`**:
```json
{
  "message": "Investigation 3fa85f64-5717-4562-b3fc-2c963f66afa6 archived successfully."
}
```

---

## 3. Blockchain Forensics API (Phase 2)

All blockchain operations target Ethereum Mainnet (`chain_id=1`) via the Etherscan API V2 abstraction. All amounts use exact decimal arithmetic (Python `Decimal`), preventing floating-point inaccuracies.

### `GET /api/v1/blockchain/status`
Checks operational connectivity to the upstream blockchain provider without leaking API keys or secrets.

- **Response `200 OK`**:
```json
{
  "provider": "etherscan_v2",
  "chain_id": 1,
  "network": "ethereum_mainnet",
  "is_configured": true,
  "key_present": true,
  "base_url": "https://api.etherscan.io/v2/api",
  "operational_status": "reachable",
  "details": {
    "latest_block_hex": "0x134e720",
    "latest_block_decimal": 20244256,
    "latency_probe": "ok"
  }
}
```

---

### `GET /api/v1/blockchain/tx/{tx_hash}`
Retrieves and normalizes an Ethereum Mainnet transaction by its 32-byte 0x-prefixed hash.

- **Parameters**:
  - `tx_hash` (path, required): 0x-prefixed 64-hex character string.
- **Response `200 OK`**: `TransactionDetailResponse` containing normalized fields (`value_wei`, `value_eth`, `gas_price_wei`, `status`, etc.).
- **Response `404 Not Found`**: Returned if the transaction does not exist on Ethereum Mainnet.
- **Response `422 Unprocessable Content`**: Returned for malformed transaction hashes.

---

### `GET /api/v1/blockchain/address/{address}/transactions`
Retrieves native ETH transaction history for an Ethereum wallet.

- **Parameters**:
  - `address` (path, required): Valid Ethereum address (checksummed, lowercase, or uppercase).
  - `limit` (query, optional, default: 25, max: 100): Number of transactions to retrieve.
  - `offset` (query, optional, default: 0): Pagination offset.
- **Response `200 OK`**: `AddressTransactionsResponse` containing normalized ETH transactions and pagination metadata.

---

### `GET /api/v1/blockchain/address/{address}/token-transfers`
Retrieves ERC-20 token transfer events for an Ethereum wallet. Token amounts are strictly segregated from native ETH.

- **Parameters**:
  - `address` (path, required): Valid Ethereum address.
  - `limit` (query, optional, default: 25, max: 100): Number of transfer events.
  - `offset` (query, optional, default: 0): Pagination offset.
- **Response `200 OK`**: `AddressTokenTransfersResponse`. Amounts are converted using actual contract decimals, or kept as raw integer units if decimals are unknown.

---

### `POST /api/v1/blockchain/investigate`
Intake endpoint to start or extend an investigation from a wallet address or transaction hash.
- Fetches real on-chain transactions and ERC-20 token events.
- Creates or attaches to an `Investigation` record.
- Persists raw and normalized data idempotently into the `evidence` table with SHA-256 tamper-detection hashes.
- Builds an evidence-backed Cytoscape.js interactive graph.

- **Request Body**:
```json
{
  "target": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
  "investigation_id": null,
  "title": "Vitalik Wallet Analysis",
  "limit": 25,
  "include_token_transfers": true
}
```

- **Response `201 Created`**:
```json
{
  "investigation_id": "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6",
  "target": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
  "target_type": "wallet_address",
  "evidence_created_count": 25,
  "evidence_skipped_duplicates_count": 0,
  "transactions_count": 20,
  "token_transfers_count": 5,
  "graph": {
    "nodes": [...],
    "edges": [...],
    "meta": {
      "total_nodes": 18,
      "total_edges": 25,
      "is_truncated": false,
      "max_nodes_reached": false,
      "max_depth_reached": false,
      "chain_id": 1,
      "investigation_id": "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6"
    }
  },
  "warnings": []
}
```

---

### `GET /api/v1/blockchain/investigations/{investigation_id}/graph`
Rebuilds the interactive Cytoscape.js graph entirely from persisted evidence records in PostgreSQL. Does not query external blockchain providers.

- **Response `200 OK`**: `CytoscapeGraphResponse`.

---

### `POST /api/v1/blockchain/investigations/{investigation_id}/expand`
Performs bounded 1-hop expansion for a specific wallet node in an existing investigation graph.
- Bounded by `max_depth` (1-2), `max_nodes` (ceiling), and `request_limit` to prevent unbounded crawling.

- **Request Body**:
```json
{
  "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
  "max_depth": 1,
  "max_nodes": 30,
  "request_limit": 10
}
```
- **Response `200 OK`**: Updated `CytoscapeGraphResponse`.
