# CryptoTrace AI — Security Architecture & Threat Model (Phase 1)

## 1. Security Architecture & Threat Boundaries

CryptoTrace AI is specifically designed for forensic investigators dealing with suspicious cryptocurrency transaction clusters, ransomware payments, and malicious binaries.

```
+-------------------------------------------------------------------------+
|                         Analyst Browser UI                              |
|   (Air-gapped / Localhost, Strict Content-Security, Local State Only)   |
+------------------------------------+------------------------------------+
                                     |
                          REST API   |  CORS Allowlist (Strict Local)
                                     v
+-------------------------------------------------------------------------+
|                     CryptoTrace AI FastAPI Backend                      |
|  - Parameterized ORM queries (SQLAlchemy 2.x)                           |
|  - Strict Pydantic v2 validation (Length, Types, Value Sanitization)    |
|  - Masked credentials in logs & diagnostics                             |
|  - Global exception interception (No stack trace leakage)               |
+-------------------+---------------------------------+-------------------+
                    |                                 |
         Async ORM  v                                 v  Provider Abstraction
+-----------------------+              +----------------------------------+
|  Local PostgreSQL DB  |              |    Decoupled Forensics Adapters  |
|  - UUID Primary Keys  |              |    - Etherscan (Phase 2)         |
|  - Cascade Protection |              |    - VirusTotal (Phase 2)        |
|  - Foreign Key Relns  |              |    - Isolated Static Sandbox     |
+-----------------------+              +----------------------------------+
```

---

## 2. Core Security Controls

### 2.1 Credential & Secret Management
- **Zero Hardcoded Secrets**: All configuration values are loaded dynamically from environment variables or `.env` using Pydantic `BaseSettings`.
- **Placeholder Defaults Only**: Repository `.env.example` contains only placeholder credentials (`changeme`).
- **Git Exclusions**: `.env`, `*.pem`, `*.key`, `__pycache__`, virtual environments, and evidence payloads are strictly excluded in `.gitignore`.
- **Diagnostic Masking**: Database connection strings in logs and health check outputs automatically redact passwords.

### 2.2 Forensic Data & Evidence Integrity
- **Immutability of Observed Evidence**:
  - Raw evidence responses from external blockchain or threat intelligence providers are stored in `raw_data` JSONB columns with a cryptographic SHA-256 integrity hash (`integrity_hash`).
  - Observed facts are strictly segregated from analytical conclusions.
- **No Speculative Heuristics**:
  - Wallets sharing an IP, transaction hop, or entity are never automatically deemed to have a common owner.
  - Multi-input clustering heuristics require explicit analyst verification before attribution is declared.
- **Non-Arbitrary Quality Assessment**:
  - Qualitative assessment statuses (`UNVERIFIED`, `PROVIDER_SUPPLIED`, `CORROBORATED`, `CONTRADICTED`, `ANALYST_CONFIRMED`, `ANALYST_REJECTED`) require an explanatory rationale.

### 2.3 Safe Static Malware Analysis Boundary
- **Isolated Static Analysis Only**: Future malware inspection (Phase 2) is designed strictly for static binary hashing, PE header inspection, and YARA string extraction.
- **No Dynamic Execution**: Uploaded samples are never executed, sandboxed dynamically, or permitted to execute code in the host operating system.
- **Upload Restrictions**: Uploaded binary artifacts are stored outside web roots and never served directly with executable MIME types.

### 2.4 Blockchain & Wallet Safety
- **No Private Key Ingestion**: The system strictly forbids collecting, asking for, or storing private keys or recovery seed phrases.
- **No Transaction Broadcasting**: CryptoTrace AI has no signing capabilities or automated fund transfer routines.
- **Read-Only / Forensics Inspection**: Analysis is performed solely on public ledger data, public address histories, and signed public receipts.

### 2.5 API & Web Application Security
- **Strict CORS Policy**: CORS middleware restricts origins to an explicit local development allowlist (`http://localhost:5173`, `http://localhost:4173`).
- **SQL Injection Prevention**: All database access executes via parameterized SQLAlchemy ORM queries and mapped expressions. Raw SQL strings are never concatenated with user inputs.
- **Error Obfuscation**: Global exception handlers catch unhandled errors and return sanitized generic messages (`INTERNAL_SERVER_ERROR`) without leaking Python traces or file system paths.
- **Input Validation**: Pydantic v2 enforces schema limits on string lengths, collection sizes, and character sets on all request payloads.

### 2.6 Blockchain Provider Security Controls (Phase 2)
- **Backend-Only Provider Credentials**: Etherscan API keys are managed exclusively in server-side configuration (`ETHERSCAN_API_KEY`). The frontend receives only processed, normalized responses.
- **Log & Error Redaction (`sanitize_url`)**: All HTTP request URLs passing through the provider adapter are filtered through `sanitize_url()`, masking any `apikey=...` parameter before debug logging or error reporting.
- **Safe Operational Status Surface**: The `/api/v1/blockchain/status` endpoint exposes only safe status indicators (`ready`, `reachable`, `unconfigured`, `degraded`) and block numbers, completely omitting API credentials.
- **Bounded Resource Budgets**: Crawl depth is restricted to 1 hop, graph nodes are capped at `max_nodes` (default 50), and query limits are bounded to protect both client browsers and provider quotas.
- **Tamper-Detection Hash Scope Notice**: The SHA-256 hash calculated on the canonical JSON payload detects subsequent unauthorized database record modification or accidental byte corruption. The application documentation and schema descriptions explicitly state that the hash does not certify the veracity of the external provider's historical records.
