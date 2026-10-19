# CryptoTrace AI — Blockchain Forensics Platform (Phase 2)

**CryptoTrace AI** is a local-first, modular forensic intelligence platform for blockchain transaction analysis, cryptocurrency hop tracing, threat intelligence correlation, and safe static malware artifact analysis.

---

## 1. System Architecture Overview

CryptoTrace AI is built as a modular monolith adhering to forensic chain-of-custody principles:
- **Strict Data Segregation**: Raw observed facts (transaction hashes, blockchain receipts, timestamps) are strictly separated from heuristic conclusions or analyst notes.
- **Provider Abstraction**: Blockchain (Etherscan V2), threat intel (VirusTotal), and malware static analysis are abstracted behind decoupled adapter interfaces.
- **Read-Only Forensic Engine**: Purely observational investigation of Ethereum Mainnet. No wallet connection, automated transaction signing, or private key ingestion is permitted.
- **Evidence Idempotency**: Duplicate evidence ingesting is guarded by partial unique indexing, preserving original raw payloads without mutation.
- **Zero Binary Float Inaccuracies**: All cryptocurrency quantities are evaluated using exact Python `Decimal` arithmetic.
- **Tamper-Detection Hashing**: Canonical JSON serialization paired with SHA-256 integrity checksums.

Detailed documentation:
- Architecture & Domain Model: [`docs/architecture.md`](docs/architecture.md)
- REST API Reference: [`docs/api.md`](docs/api.md)
- Security Model & Threat Boundary: [`docs/security.md`](docs/security.md)

---

## 2. Technology Stack

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI (versioned `/api/v1` routes)
- **Data Validation**: Pydantic v2
- **ORM & DB**: SQLAlchemy 2.x async ORM with `asyncpg`, synchronous `psycopg2` for Alembic migrations
- **Cryptography**: Pure-Python Keccak-256 implementation (zero external C-extension build requirements)
- **Migrations**: Alembic (2 versioned schema migrations)
- **Testing**: Pytest, HTTPX, AnyIO, AsyncIO (99 passing unit & integration tests)

### Frontend
- **Framework**: React 18 with TypeScript in strict mode
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with dark cyber-intelligence forensic palette
- **Graph Engine**: Cytoscape.js interactive visualization with bounded expansion controls
- **Routing**: React Router v7
- **Server State**: TanStack Query (React Query v5)
- **Testing**: Vitest & React Testing Library (16 passing component tests)

### Database
- **Primary**: Local PostgreSQL 16+ installation
- **Container Alternative**: Docker Compose included for rapid local PostgreSQL startup

---

## 3. Quick Start (Windows PowerShell)

### Step 1: Clone and Configure Environment

```powershell
# Copy environment configuration
Copy-Item .env.example .env
Copy-Item .env.example backend\.env
Copy-Item .env.example frontend\.env
```

Review and adjust credentials in `.env` as needed.

---

### Step 2: Database Setup

#### Option A: Using Docker Compose (Quickest)
```powershell
docker compose up -d
```

#### Option B: Using Local PostgreSQL Installation
Connect to PostgreSQL via `psql` or pgAdmin and run:
```sql
CREATE USER cryptotrace_user WITH PASSWORD 'changeme';
CREATE DATABASE cryptotrace_db OWNER cryptotrace_user;
GRANT ALL PRIVILEGES ON DATABASE cryptotrace_db TO cryptotrace_user;
```

---

### Step 3: Backend Setup & Migrations

```powershell
# Navigate to backend
cd backend

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .[dev]

# Run database schema migrations
alembic upgrade head

# Start FastAPI backend server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend will be accessible at:
- **API Base**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health` and `http://localhost:8000/api/v1/health`

---

### Step 4: Frontend Setup & Startup

Open a second PowerShell terminal:

```powershell
# Navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

Frontend application will be accessible at:
- `http://localhost:5173`

---

## 4. Verification & Testing

### Running Backend Tests
From the root workspace directory or `backend/`:

```powershell
# Run backend pytest suite (unit + integration tests)
.\backend\.venv\Scripts\pytest.exe backend/tests -v
```

Expected output:
```
backend/tests/integration/test_api.py (8 passed)
backend/tests/integration/test_blockchain_api.py (12 passed)
backend/tests/unit/test_ethereum_utils.py (40 passed)
backend/tests/unit/test_etherscan_adapter.py (28 passed)
backend/tests/unit/test_schemas.py (11 passed)
======================== 99 passed in 1.74s ========================
```

### Running Frontend Tests & Production Build
From `frontend/`:

```powershell
# Run Vitest component tests
npm test

# Run strict TypeScript check and production build
npm run build
```

Expected output:
```
Test Files  5 passed (5)
Tests       16 passed (16)
✓ built in 18.69s
```

---

## 5. Capabilities Delivered

### Phase 1: Full-Stack Monolith Foundation
1. **Forensic Operations Dashboard**:
   - Total investigations, active traces, evidence count, and critical priority metrics.
   - Real-time status breakdown and recent investigations table.
   - Forensic integrity warning notices and zero-wallet execution safeguards.
2. **Investigations Management**:
   - Create, list, search, filter, view details, and archive investigations.
   - Strict input validation on titles, priority, status, reference IDs, and tags.
   - Comprehensive error, empty, and loading states.
3. **Evidence Taxonomy & Explorer**:
   - Domain model ready for blockchain transactions, wallet entities, network artifacts, and malware IOCs.
   - Cryptographic integrity hashing (`integrity_hash`) and qualitative assessment rationales.
4. **Settings & Diagnostics**:
   - Live health probe testing FastAPI status, PostgreSQL connection pool, and Etherscan operational state.

### Phase 2: Real Blockchain Intelligence Engine
1. **Ethereum Mainnet Read-Only Forensics**:
   - Query native ETH transaction histories and ERC-20 token transfer events using Etherscan API V2 multichain endpoints (`chainid=1`).
   - Exact Python `Decimal` cryptocurrency unit conversion (Wei to Ether, ERC-20 token decimals). Zero floating-point drift.
   - Address validation accepting all-lowercase, all-uppercase, and enforcing EIP-55 checksumming on mixed-case addresses.
   - 32-byte 0x-prefixed transaction hash validation and normalization.
2. **Evidence Idempotency & Provenance**:
   - PostgreSQL partial unique index (`uq_evidence_investigation_type_ref`) prevents duplicate evidence insertion while protecting existing raw data from being overwritten.
   - Pre-seeded Etherscan Ethereum Mainnet evidence source (`etherscan_ethereum_mainnet`).
   - Deterministic canonical JSON serialization and SHA-256 tamper-detection hashing.
3. **Cytoscape.js Interactive Graph Visualization**:
   - Nodes color-coded and shaped by type (`wallet`, `contract`, `transaction`, `token_contract`).
   - Directed edges representing observed ETH and ERC-20 token flows with evidence linkages.
   - Interactive zoom controls, fullscreen toggle, and selected node inspector.
   - Bounded 1-hop expansion with hard node ceilings to prevent infinite graph crawling.
4. **Multi-Tab Transaction Explorer**:
   - Dedicated tabs for native ETH transfers and ERC-20 token events.
   - Formatted timestamps, gas fee calculations, Etherscan external deep-links, and one-click clipboard copying.

---

## 6. Troubleshooting

- **`greenlet` missing error**: Ensure `greenlet>=3.0.0` is installed in your virtual environment (required for SQLAlchemy 2.0 async engine).
- **PostgreSQL connection refused**: Verify PostgreSQL is running on port 5432 and credentials in `.env` match your database.
- **CORS error in browser**: Ensure `CORS_ORIGINS` in `backend/.env` includes `http://localhost:5173`.
- **Database health degraded**: If PostgreSQL is temporarily down, the app remains responsive with `GET /health` returning `200 OK` and `GET /api/v1/health` returning `degraded` without crashing.
