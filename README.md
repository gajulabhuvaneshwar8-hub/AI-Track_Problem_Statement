# AI-Powered Payment Reconciliation & Exception Management Agent

> **Hackathon Project · AI Finance Controller Track**

Automated financial reconciliation, anomaly detection and AI-powered exception management — built on FastAPI, React, PostgreSQL, and a pluggable LLM service.

---

## Table of Contents

1. [Project Purpose](#1-project-purpose)
2. [Technology Stack](#2-technology-stack)
3. [Folder Structure](#3-folder-structure)
4. [Backend Setup](#4-backend-setup)
5. [Frontend Setup](#5-frontend-setup)
6. [PostgreSQL Setup](#6-postgresql-setup)
7. [Environment Variables](#7-environment-variables)
8. [Running the Frontend](#8-running-the-frontend)
9. [Running the Backend](#9-running-the-backend)
10. [Current Implementation Status](#10-current-implementation-status)
11. [Core Reconciliation Engine](#11-core-reconciliation-engine-workflow)
12. [Backend API Reference & Endpoints](#12-backend-api-reference)
13. [Database Architecture](#13-database-architecture)
14. [AI Mismatch Analysis & Copilot](#14-ai-mismatch-analysis--investigation)
15. [Autonomous AI Investigation Agent](#15-ai-reconciliation-investigation-agent-step-7)
16. [Exception Management & Human-in-the-Loop Workflow](#16-exception-management--human-in-the-loop-workflow-step-9)
17. [Production Demonstration & Step 10 Polish](#17-production-demonstration--step-10-polish)
18. [Production Limitations & Real-World Considerations](#18-production-limitations--real-world-considerations)
19. [Documentation Directory Map](#19-documentation-directory-map)

---

## 1. Project Purpose

Modern treasury and finance teams waste thousands of hours manually matching payment records, chasing down discrepancies, and triaging exceptions. This agent automates that workflow end-to-end:

- **Automated reconciliation** — rules-based + ML matching engine across ledgers and bank statements.
- **Anomaly detection** — statistical and ML-powered outlier detection on transaction streams.
- **AI exception management** — LLM surfaces root causes and recommended actions for unresolved exceptions.
- **Audit trail** — every match, exception, and resolution stored in PostgreSQL with full provenance.

---

## 2. Technology Stack

| Layer       | Technology                                          |
|-------------|-----------------------------------------------------|
| Frontend    | React 19, Vite 8, Tailwind CSS v4, React Router, Axios, Recharts |
| Backend     | Python 3.12, FastAPI, SQLAlchemy 2, Pydantic v2, Alembic |
| Database    | PostgreSQL 16                                       |
| Auth        | JWT (python-jose)                                   |
| AI/ML       | Pandas, NumPy, Scikit-learn; LLM via pluggable service |
| Dev tooling | Docker Compose, pytest                              |

---

## 3. Folder Structure

```
AI-Payment-Reconciliation-Agent/
├── frontend/
│   └── src/
│       ├── components/       # Reusable UI components
│       ├── pages/            # Route-level page components
│       ├── layouts/          # Shared layouts (Step 2)
│       ├── services/         # API service layer (Axios)
│       ├── hooks/            # Custom React hooks
│       ├── utils/            # Pure utility functions (Step 2)
│       └── types/            # Type definitions (Step 2)
│
├── backend/
│   ├── app/
│   │   ├── api/routes/       # FastAPI route handlers (thin)
│   │   ├── api/dependencies  # Shared FastAPI Depends
│   │   ├── core/             # Config, security utilities
│   │   ├── db/               # SQLAlchemy engine + session
│   │   ├── models/           # ORM models (Step 2)
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── reconciliation/  # Core reconciliation engine (Step 2)
│   │   │   ├── ai/              # Pluggable LLM adapter (Step 2)
│   │   │   └── agents/          # AI agent orchestration (Step 2)
│   │   └── utils/            # Shared helpers
│   ├── alembic/              # Database migrations
│   └── tests/                # pytest test suite
│
├── data/
│   ├── sample/               # Seed / test data
│   └── uploads/              # Runtime file uploads
│
├── docs/                     # Architecture & API docs
├── docker-compose.yml        # PostgreSQL (Step 1)
└── README.md
```

---

## 4. Backend Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 16 (via Docker Compose or local install)

### Install dependencies

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Configure environment

```bash
# Copy the example file and edit values
cp .env.example .env
```

Edit `backend/.env` — see [Environment Variables](#7-environment-variables).

---

## 5. Frontend Setup

### Prerequisites

- Node.js 20+

### Install dependencies

```bash
cd frontend
npm install
```

---

## 6. PostgreSQL Setup

Start PostgreSQL using Docker Compose (recommended):

```bash
# From project root
docker compose up -d postgres
```

Verify it is running:

```bash
docker compose ps
```

### Run migrations

Once the database is up and the backend `.env` is configured:

```bash
cd backend
alembic upgrade head
```

---

## 7. Environment Variables

### `backend/.env`

| Variable                      | Description                                      | Example                                            |
|-------------------------------|--------------------------------------------------|----------------------------------------------------|
| `ENVIRONMENT`                 | Runtime mode                                     | `development`                                      |
| `DATABASE_URL`                | SQLAlchemy connection string                     | `postgresql+psycopg://user:pass@localhost/db`      |
| `JWT_SECRET`                  | Secret key for JWT signing                       | run `openssl rand -hex 32`                         |
| `JWT_ALGORITHM`               | JWT algorithm                                    | `HS256`                                            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime                                   | `60`                                               |
| `AI_API_KEY`                  | LLM provider API key (Step 2)                   | `sk-…`                                             |
| `AI_SERVICE_URL`              | LLM service base URL (Step 2)                   | `https://api.openai.com/v1`                        |
| `ALLOWED_ORIGINS`             | CORS allowed origins (JSON list)                 | `["http://localhost:5173"]`                        |

### Root `.env` (docker-compose)

| Variable            | Description              | Default             |
|---------------------|--------------------------|---------------------|
| `POSTGRES_DB`       | Database name            | `reconciliation_db` |
| `POSTGRES_USER`     | Database user            | `reconcile_user`    |
| `POSTGRES_PASSWORD` | Database password        | `reconcile_pass`    |
| `POSTGRES_PORT`     | Host port binding        | `5432`              |

> ⚠️ **Never commit `.env` files to version control.**

---

## 8. Running the Frontend

```bash
cd frontend
npm run dev
```

Opens at **http://localhost:5173**

---

## 9. Running the Backend

```bash
cd backend

# Activate venv first
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| Endpoint             | Description          |
|----------------------|----------------------|
| `GET /api/health`    | Service health check |
| `GET /api/docs`      | Swagger UI           |
| `GET /api/redoc`     | ReDoc UI             |

---

## 10. Current Implementation Status

### ✅ Step 1 — Foundation (COMPLETE)

- [x] Project folder structure
- [x] FastAPI app with CORS
- [x] `GET /api/health` endpoint
- [x] SQLAlchemy database configuration (no business tables yet)
- [x] Alembic migration scaffold
- [x] JWT security utilities
- [x] Pluggable AI service abstraction (stub)
- [x] React + Vite frontend scaffolded
- [x] Tailwind CSS v4 configured
- [x] React Router configured
- [x] Axios API service with interceptors
- [x] Backend health status indicator in frontend
- [x] Docker Compose (PostgreSQL)
- [x] Environment variable configuration
- [x] `.gitignore`

### ✅ Step 2 — Database Architecture (COMPLETE)

- [x] `enums.py` — all enum types (UserRole, TransactionStatus, TransactionSource, SettlementStatus, MatchStatus, ExceptionSeverity, ExceptionStatus)
- [x] `user.py` — User ORM model with role-based access control
- [x] `merchant.py` — Merchant ORM model
- [x] `transaction.py` — Transaction model (Numeric money, indexed references)
- [x] `bank_transaction.py` — BankTransaction model (indexed bank_reference)
- [x] `settlement.py` — Settlement model with full fee/tax/chargeback breakdown
- [x] `reconciliation_result.py` — ReconciliationResult with confidence score
- [x] `exception.py` — PaymentException with severity/status workflow
- [x] `audit_log.py` — Append-only AuditLog with JSON details
- [x] SQLAlchemy relationships and foreign keys wired
- [x] Alembic initial migration (`0001_initial_schema.py`)
- [x] pytest model tests — 22/22 passing (SQLite in-memory)
- [x] SQLAlchemy upgraded to 2.0.52 (Python 3.14 compatibility)

### ✅ Step 3 — Backend API Layer (COMPLETE)

- [x] Pydantic schemas for all 8 entities (Decimal money, EmailStr, enums)
- [x] Service layer: `user_service`, `merchant_service`, `transaction_service`, `bank_transaction_service`, `settlement_service`, `exception_service`, `audit_service`
- [x] FastAPI routers: `/auth`, `/merchants`, `/transactions`, `/bank-transactions`, `/settlements`, `/exceptions`, `/reconciliation` (stub)
- [x] JWT authentication: register, login, `GET /auth/me`
- [x] Role-based dependencies: `get_current_user`, `require_admin`, `require_finance_or_admin`
- [x] Pagination on transactions, bank-transactions, exceptions, reconciliation results
- [x] Filters on transactions (status, source, gateway, payment_method, merchant_id, date range)
- [x] Filters on bank-transactions (bank_name, status, date range)
- [x] Filters on exceptions (severity, category, status, assigned_to)
- [x] Global unhandled exception handler (never leaks stack traces)
- [x] Consistent HTTP status codes (201/200/204/400/401/403/404/422/500)
- [x] Swagger UI at `/api/docs`, ReDoc at `/api/redoc`
- [x] Dependencies: `python-multipart`, `pydantic[email]`, `email-validator`, `bcrypt<5.0` (passlib compat)
- [x] **69/69 tests passing** (22 model tests + 47 API tests)

### ✅ Step 4 — CSV/Excel Ingestion Engine (COMPLETE)

- [x] Multi-format file ingestion (CSV, XLSX)
- [x] Gateways: Razorpay, Stripe, Paytm, Custom
- [x] Bank statement parsers: HDFC, ICICI, SBI, Axis, Custom
- [x] Data cleaning, normalization, duplicate row rejection
- [x] `import_batches` database tracking and audit logs
- [x] Frontend drag-and-drop file import UI (`/import`)

### ✅ Step 5 — Core Deterministic Reconciliation Engine (COMPLETE)

- [x] 3-tier matching hierarchy (Exact ref → Normalized ref → Amount + Date tolerance)
- [x] Anomaly detection (amount mismatch, missing in bank/gateway, duplicates, settlement delays, status mismatch)
- [x] Idempotent reconciliation runs
- [x] Full reconciliation endpoints (`POST /api/reconciliation/run`, `/results`, `/summary`)
- [x] Interactive Reconciliation dashboard UI (`/reconciliation`)
- [x] 112/112 tests passing

### ✅ Step 6 — AI Mismatch Analysis & Investigation (COMPLETE)

- [x] Interpretive AI analysis layer (`app/services/ai/`)
- [x] Strict domain boundary: AI **never** modifies reconciliation outcomes or financial amounts
- [x] Robust deterministic fallback analyzer (`fallback_analyzer.py`) when AI is unavailable or unconfigured
- [x] 7 anomaly categories handled: Amount mismatch, Missing bank/gateway, Duplicates, Delays, Status mismatch, Unresolved
- [x] `ai_analyses` database table, Alembic migration `0003_add_ai_analyses.py`
- [x] Endpoints under `/api/ai/*` (analyze, investigate, history, filter)
- [x] Duplicate analysis prevention with `?force=true` re-analysis support
- [x] Frontend AI Mismatch Analysis page (`/ai-analysis`) and Reconciliation table integration
- [x] **138/138 tests passing** (26 dedicated AI tests, fully mocked LLM)

### ✅ Step 7 — Autonomous AI Investigation Agent (COMPLETE)

- [x] Autonomous multi-ledger evidence aggregation across 6 data sources
- [x] Deterministic risk assessment and decision engine (`MONITOR`, `REVIEW`, `ESCALATE`)
- [x] Gemini LLM narrative synthesis with robust offline fallback analyzer
- [x] Automated escalation routing with team assignments
- [x] Strict non-mutability financial invariants (read-only on core ledgers)
- [x] Endpoints under `/api/agents/*` (investigate, list, single, evidence, escalation)
- [x] Frontend Agent Investigation workbench (`/agent-investigation`)
- [x] **168/168 tests passing** (30 dedicated agent tests)

### ✅ Step 8 — Finance Operations Control Center (COMPLETE)

- [x] Production-grade UI theme and design system
- [x] Dynamic dashboard metrics and reconciliation health monitor
- [x] Transaction statistics, charts, and filtering
- [x] AI analysis inspection and agent launch flows
- [x] Audit log viewer and settlement tracking
- [x] End-to-end frontend build verification (`npm run build`)

### ✅ Step 9 — Exception Management & Human-in-the-Loop Workflow (COMPLETE)

- [x] Workflow state machine (`open` → `investigating` → `resolved`/`ignored`, assignment, review notes, internal escalation, and supervisor reopening)
- [x] Strict HITL guardrails: AI recommends; human operator makes final decisions; strictly zero amount or ledger tampering
- [x] Real-time chronological timeline grounded in multi-table DB events (`PaymentException`, `AuditLog`, `AIAnalysis`, `AgentInvestigation`)
- [x] Human review REST endpoints under `/api/v1/exceptions`:
  - `POST /{id}/assign` — Assign/reassign to operators
  - `POST /{id}/status` — Status transition with optional note
  - `POST /{id}/review` — Append progress review notes
  - `POST /{id}/resolve` — Mandatory resolution note required
  - `POST /{id}/ignore` — Mandatory rationale required
  - `POST /{id}/escalate` — Internal team escalation
  - `POST /{id}/reopen` — Supervisor reopening of terminal tickets
  - `GET /{id}/timeline` — Grounded chronological audit timeline
  - `GET /{id}/details` — 360° projection with related transactions, bank data, AI analyses, and agent investigations
  - `GET /workflow-summary` — Real-time metrics strip
  - `GET /assignees` — Assigned operator list
- [x] Comprehensive tamper-evident audit logging for every lifecycle event
- [x] Production Frontend Exception Workbench (`/exceptions`) with 360° slide-out inspector, inline assignment, tabbed review/resolution/escalation panels, and Dashboard summary strip
- [x] **200/200 tests passing** (26 dedicated Step 9 integration tests in `test_api_exceptions_workflow.py`)

### ✅ Step 10 — Production Demo Readiness & Polish (COMPLETE)

- [x] **10 Real-World Edge Case Datasets**: Curated demonstration data under `data/sample/` (`gateway_transactions.csv`, `bank_transactions.csv`, `settlements.csv`) covering exact matches, normalized references, case variations, fee discrepancies, missing records, duplicates, delayed deposits, status conflicts, recurring fee patterns, and high-value exceptions ($15,000+).
- [x] **Comprehensive End-to-End Test Suite**: Dedicated suite in `backend/tests/test_end_to_end_workflow.py` with 18 comprehensive tests verifying full lifecycle workflows, AI & agent fallbacks, RBAC isolation, and repeated run idempotency.
- [x] **218/218 Tests Passing**: Zero regressions across all models, services, APIs, engines, and agents (`pytest tests/ -v`).
- [x] **Admin Demo Loading Route**: `POST /api/demo/load-sample-data` allowing one-click idempotent sample data loading for live demonstrations.
- [x] **Frontend Code Splitting & Performance**: Dynamic route splitting in `src/App.jsx` using `React.lazy` and `React.Suspense`. All asset chunks optimized under 400 kB with zero Vite bundle size warnings.
- [x] **Full Production Documentation**: Detailed guides in [`docs/demo-guide.md`](docs/demo-guide.md), [`docs/testing.md`](docs/testing.md), and [`docs/architecture.md`](docs/architecture.md).

---

## 12. Backend API Reference

### Start the backend

```powershell
# 1. Start PostgreSQL
docker compose up -d postgres

# 2. Apply migrations
cd backend
alembic upgrade head

# 3. Start the dev server
.venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

| URL | Description |
|-----|-------------|
| `http://localhost:8000/api/docs` | Swagger UI (interactive) |
| `http://localhost:8000/api/redoc` | ReDoc (reference) |
| `http://localhost:8000/api/openapi.json` | Raw OpenAPI schema |

### Authentication Flow

```bash
# 1. Register
POST /api/auth/register
{"name": "Alice", "email": "alice@company.com", "password": "SecurePass1", "role": "admin"}

# 2. Login → get token
POST /api/auth/login
{"email": "alice@company.com", "password": "SecurePass1"}
# Response: {"access_token": "eyJ...", "token_type": "bearer", "user": {...}}

# 3. Use token on protected endpoints
Authorization: Bearer <access_token>
```

### API Endpoints

```
/api
 ├── /auth
 │    ├── POST   /register       Create a new user account
 │    ├── POST   /login          Authenticate → JWT token
 │    └── GET    /me             Current user profile (protected)
 │
 ├── /merchants
 │    ├── POST   /               Create merchant (auth required)
 │    ├── GET    /               List all merchants
 │    ├── GET    /{id}           Get merchant by ID
 │    ├── PUT    /{id}           Update merchant
 │    └── DELETE /{id}          Delete merchant → 204
 │
 ├── /transactions
 │    ├── POST   /               Create transaction
 │    ├── GET    /               List + filter (status, source, gateway,
 │    │                          merchant_id, payment_method, date_from, date_to)
 │    │                          Paginated: ?page=1&page_size=20
 │    ├── GET    /{id}           Get transaction
 │    ├── PUT    /{id}           Update transaction
 │    └── DELETE /{id}          Delete transaction → 204
 │
 ├── /bank-transactions
 │    ├── POST   /                      Create bank transaction
 │    ├── GET    /                      List + filter (bank_name, status, date_from, date_to)
 │    │                                 Paginated: ?page=1&page_size=20
 │    ├── GET    /{id}                  Get bank transaction
 │    ├── PUT    /{id}                  Update bank transaction
 │    └── DELETE /{id}                  Delete → 204
 │
 ├── /settlements
 │    ├── POST   /                      Create settlement
 │    ├── GET    /                      List settlements (?merchant_id=...)
 │    └── GET    /{id}                  Get settlement
 │
 ├── /exceptions
 │    ├── POST   /                      Create exception
 │    ├── GET    /                      List + filter (severity, category, status, assigned_to)
 │    │                                 Paginated: ?page=1&page_size=20
 │    ├── GET    /workflow-summary      Summary metrics (open, investigating, resolved, etc.)
 │    ├── GET    /assignees             List of assigned operators
 │    ├── GET    /{id}                  Get exception
 │    ├── GET    /{id}/details          360° projection with txns, bank data, AI, investigations
 │    ├── GET    /{id}/timeline         Grounded chronological event timeline
 │    ├── POST   /{id}/assign           Assign or reassign operator
 │    ├── POST   /{id}/status           Update status (open, investigating) with optional note
 │    ├── POST   /{id}/review           Append review notes
 │    ├── POST   /{id}/resolve          Resolve exception (note required)
 │    ├── POST   /{id}/ignore           Ignore exception (reason required)
 │    ├── POST   /{id}/escalate         Internal escalation with reason
 │    ├── POST   /{id}/reopen           Reopen resolved/ignored exception
 │    └── PUT    /{id}                  Update exception attributes
 │
 ├── /agents
 │    ├── POST   /investigate/exception/{id}       Autonomous exception investigation
 │    ├── POST   /investigate/reconciliation/{id}  Autonomous reconciliation investigation
 │    ├── GET    /investigations                   List investigations with filters
 │    ├── GET    /investigations/{id}              Get single investigation
 │    ├── GET    /investigations/{id}/evidence     Multi-ledger corroborating evidence
 │    └── GET    /investigations/{id}/escalation   Escalation routing advice
 │
 ├── /reconciliation
 │    ├── POST   /run            Trigger reconciliation for merchant
 │    ├── GET    /results        List reconciliation results (paginated)
 │    ├── GET    /results/{id}   Get reconciliation result
 │    └── GET    /summary/{id}   Get reconciliation statistics
 │
 ├── /ai
 │    ├── POST   /analyze/{id}   AI analysis of reconciliation result
 │    ├── POST   /analyze/exception/{id}  AI analysis of exception ticket
 │    ├── POST   /investigate/{id} Deep diagnostic investigation & checklist
 │    ├── GET    /analyses       List historical AI analyses with filters
 │    ├── GET    /analyses/{id}  Get single AI analysis
 │    └── GET    /analyses/reconciliation/{id} History for reconciliation
 │
 └── /health                    Service health check (no auth required)
```

### Run Tests

```powershell
cd backend
.venv\Scripts\activate
pytest tests/ -v

# Output: 218 passed (22 model + 47 API + 43 ingestion/recon + 26 AI + 30 agent + 26 workflow + 18 E2E tests)
# No Postgres needed — uses SQLite in-memory with transactional isolation
```

### Pagination Response Format

```json
{
  "items": [...],
  "page": 1,
  "page_size": 20,
  "total": 147
}
```

### Error Response Format

```json
{"detail": "Merchant not found"}
```


---

## 11. Database Architecture

### Entity Overview

| Table | Purpose | Key Relationships |
|---|---|---|
| `users` | Platform users (admin / finance_user) | → `exceptions` (assignee), → `audit_logs` |
| `merchants` | Business entities processing payments | → `transactions`, → `settlements` |
| `transactions` | Payment records from gateway/bank/order | → `merchants`, → `reconciliation_results` |
| `bank_transactions` | Bank statement records | → `reconciliation_results` |
| `settlements` | Settlement batches from processor to merchant | → `merchants` |
| `reconciliation_results` | Match outcome between transactions & bank records | → `transactions`, → `bank_transactions`, → `exceptions` |
| `exceptions` | Reconciliation exceptions needing review | → `reconciliation_results`, → `users` (assignee) |
| `audit_logs` | Append-only action trail | → `users` (nullable) |

### Relationship Diagram

```
users ──────────────────────────────────────────────┐
  │                                                  │ assigned_to
  │ (audit_logs.user_id)                             ▼
  └──────────────────────────► audit_logs       exceptions
                                               ▲        ▲
merchants ─────────────┐                       │        │ (reconciliation_id)
  │                    │                       │        │
  │ (merchant_id)      │ (merchant_id)         │   reconciliation_results
  ▼                    ▼                       │        ▲        ▲
transactions        settlements                │        │        │
  │                                            │ (transaction_id) │ (bank_transaction_id)
  │                                            │        │        │
  └──────────────────────────────────────────► │  transactions   bank_transactions
```

### Money / Decimal Precision

All monetary columns use **`Numeric(18, 4)`** — never `Float`. This ensures:

- Exact representation of currency amounts (up to 4 decimal places)
- No floating-point rounding errors in financial calculations
- Python's `decimal.Decimal` type on the application side

**Confidence scores** use `Numeric(5, 4)` — values between `0.0000` and `1.0000`.

### Enum Types (PostgreSQL native)

| Enum | Values |
|---|---|
| `userrole` | `admin`, `finance_user` |
| `transactionstatus` | `success`, `failed`, `pending`, `refunded`, `disputed` |
| `transactionsource` | `gateway`, `bank`, `order` |
| `settlementstatus` | `pending`, `settled`, `failed` |
| `matchstatus` | `matched`, `partial_match`, `amount_mismatch`, `missing_in_bank`, `missing_in_gateway`, `duplicate`, `unresolved` |
| `exceptionseverity` | `low`, `medium`, `high`, `critical` |
| `exceptionstatus` | `open`, `investigating`, `resolved`, `ignored` |

### Indexes

| Table | Indexed Columns | Purpose |
|---|---|---|
| `users` | `email` | Fast auth lookup |
| `merchants` | `email` | Uniqueness check |
| `transactions` | `transaction_reference`, `order_reference`, `transaction_date`, `merchant_id` | Reconciliation matching |
| `bank_transactions` | `bank_reference`, `transaction_reference`, `transaction_date` | Bank lookup & matching |
| `settlements` | `settlement_reference`, `settlement_date`, `merchant_id` | Settlement queries |
| `reconciliation_results` | `transaction_id`, `bank_transaction_id`, `match_status`, `reconciled_at` | Exception routing |
| `exceptions` | `reconciliation_id`, `status`, `severity`, `assigned_to`, `created_at` | Dashboard filtering |
| `audit_logs` | `user_id`, `(entity_type, entity_id)`, `created_at`, `action` | Audit trail queries |

### Running the Migration

```bash
# 1. Start PostgreSQL
docker compose up -d postgres

# 2. Apply all migrations
cd backend
alembic upgrade head

# 3. Verify schema
alembic current

# 4. Rollback (if needed)
alembic downgrade -1
```

### Running Model Tests

Tests use SQLite in-memory — **no PostgreSQL required**:

```bash
cd backend
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pytest tests/ -v
# 112 passed
```

---

## 11. Core Reconciliation Engine Workflow

The deterministic reconciliation engine matches Gateway Transactions against Bank Statements:

1. **Ingest Data**: Upload transaction files via `/import` or API (`/api/ingestion/*`).
2. **Execute Reconciliation**: Trigger matching via `/reconciliation` or `POST /api/reconciliation/run`:
   - **Level 1**: Exact Reference Match (`TXN001` == `TXN001`)
   - **Level 2**: Normalized Reference Match (`TXN-001` → `TXN001`)
   - **Level 3**: Amount + Date Fallback (±1 day tolerance, single candidate only)
3. **Anomalies Captured**:
   - `amount_mismatch`: Amount discrepancy calculated using `Decimal`
   - `missing_in_bank`: Gateway payment without bank statement deposit
   - `missing_in_gateway`: Bank statement deposit without gateway record
   - `duplicate`: Duplicate transaction references flagged
   - `settlement_delay`: Settlement delays > 1 day marked, > 3 days flagged as exceptions
   - `status_mismatch`: Gateway success with Bank failure flagged as critical exception
4. **Idempotency**: Rerunning reconciliation updates existing results rather than duplicating records.
5. **Dashboard & Results**: Inspect results with accuracy metrics at `http://localhost:5173/reconciliation`.

---

## 12. AI Mismatch Analysis & Investigation

The AI Mismatch Analysis layer provides interpretive diagnostics for reconciliation discrepancies without compromising financial data integrity.

### Architecture & Separation of Concerns

```
[ Reconciliation Result ]  ───>  [ Exception Ticket ]
                                         │
                                         ▼
                               [ AI Analysis Service ]
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
          [ AI Provider (LLM) ]                     [ Fallback Analyzer ]
          (Sanitized Context JSON)                  (Rule-based deterministic engine)
                   │                                           │
                   ▼                                           ▼
        [ Response Validation ]                                │
                   │                                           │
                   └─────────────────────┬─────────────────────┘
                                         ▼
                             [ ai_analyses Database ]
                                         │
                                         ▼
                           [ React UI (/ai-analysis) ]
```

### Key Principles:
- **Deterministic Truth**: The deterministic engine is the sole source of financial truth.
- **AI Is Strictly Advisory**: AI **never** marks transactions as matched, changes amounts, resolves exceptions, or creates financial transactions.
- **Zero-Failure Fallback**: If `AI_API_KEY` is absent, times out (>30s), or errors, `fallback_analyzer.py` automatically generates a deterministic explanation (`status="fallback"`, `ai_provider="fallback"`). The API never returns HTTP 500 on AI unavailability.
- **Analysis History & Duplicate Prevention**: Complete audit history is retained in `ai_analyses`. Identical requests return cached analyses unless `?force=true` is requested.
- **7 Core Discrepancies**: Amount mismatch, Missing in bank, Missing in gateway, Duplicate, Delayed settlement, Status mismatch (critical risk), Unresolved.
- Detailed architecture and design guide in [`docs/ai_analysis.md`](docs/ai_analysis.md).
 
---
 
## 13. AI Reconciliation Investigation Agent (Step 7)
 
 The **AI Reconciliation Investigation Agent** acts as an autonomous finance operations assistant. It ingests exceptions or reconciliation results, gathers cross-ledger evidence, applies deterministic financial decision rules, synthesizes natural language explanations, and routes escalations with immutable audit provenance.
 
 ### Architecture & Core Lifecycle
 
 1. **Trigger Reception**: Ingests `exception_id` or `reconciliation_id`. Reuses completed investigations unless `?force=true`.
 2. **Multi-Ledger Evidence Gathering**: Safe read-only extraction from 6 sources:
    - Gateway transaction records
    - Bank statement credit/debit records
    - Reconciliation engine match results
    - Settlement batch records
    - Related exception history
    - Historical AI analyses
 3. **Deterministic Decision Engine**:
    - `MONITOR`: Low-risk or expected timing window delays (<= 3 days).
    - `REVIEW`: Discrepancies requiring standard human review (amount mismatches, unmapped entries).
    - `ESCALATE`: High/critical risk, state conflicts (Gateway Success vs Bank Failed), or large variances (> ₹10,000).
 4. **AI Narrative Synthesis**: Formulates clear summaries, **confirmed facts** (grounded in ledger data), unconfirmed **hypotheses/causes**, and operator recommendations. Automatically falls back to deterministic rule-based analysis if the external LLM is unavailable.
 5. **Escalation Routing**: Automatically drafts escalation priority and routes to specialized teams (`Finance Operations`, `Payment Operations`, `Risk Team`, `Engineering`, `Merchant Support`).
 6. **Financial Guardrails**:
    - **Strict Non-Mutability**: Read-only on financial tables. Cannot modify amounts, reconciliation statuses, exceptions, or issue refunds/money movement.
    - **Merchant Isolation**: Enforces tenant boundaries where non-admin users only access investigations for authorized merchants.
    - **Full Audit Trail**: Logs events (`investigation_started`, `evidence_collected`, `escalation_created`, `investigation_completed`, `investigation_failed`) to the immutable audit log.
 
 ### Endpoints
 
 - `POST /api/agents/investigate/exception/{exception_id}`: Autonomous investigation of an exception
 - `POST /api/agents/investigate/reconciliation/{reconciliation_id}`: Autonomous investigation of a reconciliation result
 - `GET /api/agents/investigations`: List investigations with multi-attribute filters (`status`, `decision`, `risk_level`, `investigation_type`, `escalation_team`)
 - `GET /api/agents/investigations/{id}`: Single investigation detail
 - `GET /api/agents/investigations/{id}/evidence`: Full multi-ledger evidence ledger
 - `GET /api/agents/investigations/{id}/escalation`: Team routing ticket and priority recommendation
 
 ### UI Dashboard
 
 Visit `/agent-investigation` on the frontend for the interactive investigation workbench with stage progress tracking, evidence table, decision badges, and trigger dispatch.
 
 For complete architectural diagrams, refer to [`docs/agent-architecture.md`](docs/agent-architecture.md).

---

## 14. Exception Management & Human-in-the-Loop Workflow (Step 9)

Step 9 bridges automated AI investigation with human accountability. While the deterministic reconciliation engine detects mismatches and the AI agent recommends dispositions, **human finance operators remain strictly responsible for final financial outcomes**.

### Core Architecture & State Machine

```
[ Exception Created (open) ]
          │
          ├───► [ Assigned to Operator ] ───► (investigating)
          │                                         │
          │                                         ├───► [ Add Review Notes ]
          │                                         ├───► [ Internal Escalation ]
          │                                         │
          ├───► [ Mark Resolved (Note Req.) ] ◄─────┤
          │     (Terminal: resolved)                │
          │                                         │
          └───► [ Mark Ignored (Reason Req.) ] ◄────┘
                (Terminal: ignored)
                        │
                        ▼ (Supervisor Reopening)
                [ Reopened (open) ]
```

### Key Capabilities

1. **State Machine with Terminal Protection**: Transitions enforce strict validation. Tickets marked `resolved` or `ignored` cannot have statuses, notes, or assignees mutated without supervisor reopening (`POST /{id}/reopen`).
2. **Grounded Chronological Timeline**: Unifies database-backed events from `PaymentException`, `AuditLog`, `AIAnalysis`, and `AgentInvestigation` into a coherent historical sequence with relative timestamps and user tags.
3. **Tamper-Evident Audit Trail**: Every status change, assignment, note addition, resolution, and escalation writes an immutable row to `audit_logs`.
4. **Interactive Operations Workbench (`/exceptions`)**:
   - High-density filter bar (status, severity, search, assignment).
   - High-level metrics strip (`total`, `open`, `investigating`, `resolved`, `critical`, `unassigned`).
   - Inline fast operator assignment.
   - 360° slide-out inspector showing side-by-side gateway transaction vs. bank record comparison, AI confidence scores, grounded timeline, and action panels.
5. **Zero Financial Mutation Guardrail**: The workflow never modifies transaction amounts, reconciliation decisions, or money movement.

For full architectural diagrams and API schemas, see [`docs/exception-management.md`](docs/exception-management.md).

---

## 17. Production Demonstration & Step 10 Polish

Step 10 elevates the application to enterprise demonstration caliber with realistic financial edge cases, automated demonstration loading, and optimized bundle delivery.

### Instant Demo Setup Endpoint (Admin Only)

Administrators can populate realistic multi-ledger demo data in one click or API call:

```bash
POST /api/demo/load-sample-data?merchant_id=<MERCHANT_ID>
Authorization: Bearer <ADMIN_JWT>
```

This endpoint:
- Ingests `data/sample/gateway_transactions.csv` (53 records across Stripe, Razorpay, Paytm)
- Ingests `data/sample/bank_transactions.csv` (54 records across HDFC, ICICI, SBI, Axis)
- Ingests `data/sample/settlements.csv` (6 settlement batches with gross, fee, tax, chargeback, and net)
- **Guarantees Idempotency**: Repeated calls report duplicate row detections without creating orphaned transactions.

### Key Demonstrated Scenarios

1. **Exact Ref & Amount Match**: e.g., `TXN-2026-0001` matches `BNK-2026-0001` with 1.0 confidence score.
2. **Normalized Matching**: Handles space stripped (`TXN 2026 0006`) and lowercase (`txn20260007`) references.
3. **Fee Deduction Discrepancies**: e.g., `TXN-2026-0002` ($1,000.00 vs $985.00) flagged as `amount_mismatch` with exact $15 variance.
4. **Missing Gateway / Missing Bank**: e.g., `TXN-2026-0009` (missing in bank) and `BNK-2026-0012` (missing in gateway).
5. **Duplicate Bank Entries**: e.g., `TXN-2026-0011` credited twice (`BNK-2026-0011A` and `BNK-2026-0011B`).
6. **Severe Settlement Delays**: e.g., `TXN-2026-0010` booked 6 days after initiation.
7. **Status Inversion Conflicts**: e.g., `TXN-2026-0014` marked `success` at gateway but `reversed` at bank.
8. **Recurring Micro-Fee Patterns**: e.g., `TXN-2026-0003`, `TXN-2026-0018`, `TXN-2026-0027` exhibiting consistent $5 processing deductions.
9. **High-Value Discrepancy Escalation**: e.g., `TXN-2026-0053` ($15,000.00 vs $14,700.00) automatically raising `critical` severity.

For the live demonstration script and timing guide, refer to [`docs/demo-guide.md`](docs/demo-guide.md).

---

## 18. Production Limitations & Real-World Considerations

While this hackathon project implements an enterprise-grade architecture, running in full global production involves several additional infrastructural considerations:

1. **High-Throughput Distributed Streaming**: For millions of daily transactions, replace synchronous batch ingestion with distributed streaming (e.g., Apache Kafka, AWS Kinesis) and an event-driven worker pool (Celery / Temporal).
2. **Database Sharding & Partitioning**: Partition `transactions`, `bank_transactions`, and `audit_logs` by `merchant_id` and monthly date ranges to optimize query latency on multi-gigabyte datasets.
3. **Direct Banking Connectivity (Open Banking / Host-to-Host)**: Real-world deployments integrate automated SFTP / ISO 20022 XML feeds and Open Banking APIs (e.g., Plaid, Yapily, Cashfree) alongside manual CSV/XLSX imports.
4. **Hardware Security Modules (HSM) & KMS**: In production, symmetric JWT signing keys and payment processor API credentials should be managed via cloud secret managers (AWS Secrets Manager, GCP Secret Manager, HashiCorp Vault) with automated key rotation.
5. **Multi-Region Disaster Recovery**: Implement active-passive database replication with read replicas for high-volume analytics.

---

## 19. Documentation Directory Map

| Document | Path | Focus Area |
|---|---|---|
| **Live Demo Walkthrough Guide** | [`docs/demo-guide.md`](docs/demo-guide.md) | 5–7 min presentation script, credentials, and verification cheatsheet |
| **Comprehensive Testing Guide** | [`docs/testing.md`](docs/testing.md) | 218 test specifications, category breakdowns, and execution commands |
| **System Architecture & Design** | [`docs/architecture.md`](docs/architecture.md) | End-to-end component diagrams, data flows, and non-negotiable invariants |
| **Exception Management Guide** | [`docs/exception-management.md`](docs/exception-management.md) | Finite state machine, human-in-the-loop controls, and 360° inspector |
| **AI Mismatch Analysis Guide** | [`docs/ai_analysis.md`](docs/ai_analysis.md) | Advisory LLM integration and deterministic zero-failure fallback analyzer |
| **Autonomous Agent Architecture** | [`docs/agent-architecture.md`](docs/agent-architecture.md) | Multi-ledger evidence gathering, risk scoring, and automated team routing |
| **Reconciliation Engine Rules** | [`docs/reconciliation.md`](docs/reconciliation.md) | 3-tier matching hierarchy and anomaly detection specifications |
