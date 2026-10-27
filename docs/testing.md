# Comprehensive Testing Guide

> **AI-Powered Payment Reconciliation & Exception Management Agent**  
> *Test Suite Status: 218 Tests Passing | 100% Zero-Regression Record*

This document details the automated testing suite for the platform, including architecture, execution instructions, categorization, test isolation strategies, and continuous verification.

---

## 1. Test Suite Architecture

The backend test suite is constructed on top of `pytest`, `pytest-asyncio`, and FastAPI's `TestClient` (backed by Starlette and HTTPX).

### In-Memory Database Isolation
All test suites run against an **in-memory SQLite database** with transactional rollbacks between test methods (`tests/conftest.py`).
- **Zero External Dependencies**: Tests run completely isolated from any local or remote PostgreSQL instance.
- **Speed**: The entire 218-test suite completes in approximately 100–110 seconds.
- **Deterministic Reset**: Every test gets fresh tables, pre-seeded test fixtures, and clean auth state.

---

## 2. Test Categorization & Breakdown

| Test Suite File | Test Category | Count | Focus Areas |
|---|---|---|---|
| `tests/test_models.py` | ORM Models & Constraints | 22 | Schema validation, foreign keys, unique constraints, precision (`Numeric(18, 4)`) |
| `tests/test_api_auth.py` | Auth & Identity | 10 | User registration, JWT creation, token expiration, password hashing |
| `tests/test_api_merchants.py` | Multi-Tenant Merchants | 8 | Merchant CRUD, tenant isolation, cascade rules |
| `tests/test_api_transactions.py` | Transaction Ingestion API | 12 | Gateway transaction CRUD, filtering, pagination, date ranges |
| `tests/test_api_bank_transactions.py` | Bank Statement API | 8 | Bank statement CRUD, bank name filters, reference tracking |
| `tests/test_api_settlements.py` | Settlement Batches API | 9 | Settlement creation, fee/tax calculations, net calculations |
| `tests/test_api_ingestion.py` | CSV/XLSX Ingestion Engine | 20 | Multi-format parsers (Stripe, Razorpay, HDFC, ICICI), deduplication, batch tracking |
| `tests/test_reconciliation_engine.py` | Core Matching Engine | 23 | 3-tier matching, exact ref, normalized ref, tolerance matching, anomaly detection |
| `tests/test_reconciliation_api.py` | Reconciliation Endpoints | 8 | Run endpoint idempotency, match results retrieval, summary stats |
| `tests/test_ai_analysis.py` | AI Mismatch Diagnostics | 26 | Advisory AI analysis, mock LLM client, deterministic fallback analyzer, caching |
| `tests/test_agent_investigation.py` | Autonomous Agent Engine | 30 | Multi-ledger evidence gathering, risk engine (`MONITOR`/`REVIEW`/`ESCALATE`), routing |
| `tests/test_api_exceptions.py` | Exception Base API | 16 | Exception CRUD, severity/category filters, assignment |
| `tests/test_api_exceptions_workflow.py` | HITL Exception State Machine | 26 | Transition validation, mandatory review/resolution notes, reopen, 360° details, timeline |
| `tests/test_end_to_end_workflow.py` | Complete End-to-End Flows | 18 | Multi-service integration, full lifecycle, edge cases, RBAC, idempotency |
| **Total Test Count** | | **218** | **All Passing** |

---

## 3. End-to-End Test Suite (`tests/test_end_to_end_workflow.py`)

The end-to-end suite exercises the complete lifecycle across all services without mocking database operations:

1. **`test_e2e_successful_match_workflow`**: Ingests gateway and bank records → runs reconciliation → verifies match status `matched` and zero exceptions created.
2. **`test_e2e_amount_mismatch_complete_workflow`**: Ingests $1,000 gateway vs $985 bank → runs reconciliation → triggers `amount_mismatch` exception → triggers AI analysis → triggers agent investigation → assigns finance operator → adds review note → resolves with ledger adjustment note.
3. **`test_e2e_missing_in_bank_workflow`**: Unmatched gateway transaction creates `missing_in_bank` exception.
4. **`test_e2e_missing_in_gateway_workflow`**: Unmatched bank deposit creates `missing_in_gateway` exception.
5. **`test_e2e_duplicate_transaction_workflow`**: Duplicate bank statement entries flag both transactions and create duplicate exception.
6. **`test_e2e_delayed_transaction_workflow`**: Bank deposit 5 days after gateway transaction triggers `settlement_delay` exception.
7. **`test_e2e_critical_status_mismatch_workflow`**: Gateway `success` vs Bank `failed`/`reversed` triggers critical exception and immediate escalation recommendation.
8. **`test_e2e_ai_fallback_workflow`**: Simulates LLM unavailability (`RuntimeError`); verifies deterministic fallback analyzer generates valid explanation with `status="fallback"`.
9. **`test_e2e_agent_fallback_workflow`**: Simulates agent LLM timeout; verifies deterministic risk decision and multi-ledger evidence collection succeed without throwing 500.
10. **`test_e2e_human_review_workflow`**: Validates assignment to finance operator and formatted reviewer note appending.
11. **`test_e2e_escalation_workflow`**: Validates internal escalation requires a non-empty reason and sets timestamp.
12. **`test_e2e_resolution_workflow`**: Validates resolving an exception strictly requires a resolution note (rejects empty notes with HTTP 422).
13. **`test_e2e_ignore_workflow`**: Validates ignoring an exception requires a business justification and transitions status to `ignored`.
14. **`test_e2e_audit_timeline_workflow`**: Verifies chronological audit timeline records lifecycle events (assignment, review, resolution) in sequential order.
15. **`test_e2e_repeated_reconciliation_idempotency`**: Running reconciliation multiple times updates existing records and produces zero duplicate exceptions.
16. **`test_e2e_merchant_isolation_workflow`**: Enforces strict tenant isolation; merchant A cannot query or see exceptions belonging to merchant B.
17. **`test_e2e_demo_load_sample_data_endpoint`**: Verifies `POST /api/demo/load-sample-data` requires Admin role (403 for finance user) and is idempotent on repeat calls.
18. **`test_e2e_high_value_exception_workflow`**: Transactions above threshold ($10,000+) automatically trigger `high`/`critical` severity exceptions.

---

## 4. Running the Tests

### Activate Python Virtual Environment
```bash
# Windows
cd backend
.venv\Scripts\activate

# macOS / Linux
cd backend
source .venv/bin/activate
```

### Run Full Test Suite
```bash
pytest -v
```

### Run End-to-End Tests Specifically
```bash
pytest tests/test_end_to_end_workflow.py -v
```

### Run Specific Category Tests
```bash
# Model & Schema tests
pytest tests/test_models.py -v

# Core Reconciliation tests
pytest tests/test_reconciliation_engine.py tests/test_reconciliation_api.py -v

# AI Diagnostics tests
pytest tests/test_ai_analysis.py -v

# Autonomous Agent tests
pytest tests/test_agent_investigation.py -v

# Human-in-the-Loop Exceptions tests
pytest tests/test_api_exceptions_workflow.py -v
```

---

## 5. Frontend Build Verification

To verify frontend compilation, type safety, and code splitting:

```bash
cd frontend
npm run build
```

Expected output:
- Dynamic bundle splitting via `React.lazy` and `React.Suspense`.
- All generated JavaScript asset chunks remain **under 400 kB**.
- Zero chunk size warnings from Vite.
- Output directory `dist/` ready for production deployment.
