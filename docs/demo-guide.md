# End-to-End Live Demonstration Guide

> **AI-Powered Payment Reconciliation & Exception Management Agent**  
> *Estimated Presentation Duration: 5–7 Minutes*

This guide provides a step-by-step walkthrough script for evaluating or presenting the payment reconciliation platform. It highlights how deterministic financial rules, automated cross-ledger matching, interpretive AI diagnostics, and human-in-the-loop workflows operate in harmony without risking ledger integrity.

---

## Pre-Requisites & Credentials

Ensure both backend and frontend servers are running:
- **Backend API**: `http://localhost:8000` (FastAPI)
- **Frontend App**: `http://localhost:5173` (React + Vite)
- **Interactive API Docs**: `http://localhost:8000/api/docs`

### Pre-Configured Demonstration Accounts

| Role | Email | Password | Access Rights |
|---|---|---|---|
| **Admin** | `admin@reconcile.ai` | `Admin123!` | Full control, demo data loading, tenant management |
| **Finance Operator** | `finance@reconcile.ai` | `Finance123!` | Ingestion, reconciliation, exception review & resolution |

*(If running on a fresh database, register these users via the `/login` screen or the API endpoint `POST /api/auth/register`.)*

---

## Curated Demo Dataset Scenarios

The platform includes verified production-grade sample files under `data/sample/`:
1. `data/sample/gateway_transactions.csv` (Gateway transactions across Razorpay, Stripe, and Paytm)
2. `data/sample/bank_transactions.csv` (Bank statement entries from HDFC, ICICI, SBI, Axis)
3. `data/sample/settlements.csv` (Processor settlement batches with gross, fees, taxes, and net transfers)

### 10 Real-World Edge Cases Demonstrated

| Scenario | Reference | Gateway Data | Bank Statement | Expected Outcome |
|---|---|---|---|---|
| **1. Exact Match** | `TXN-2026-0001` | $1,250.00 (Success) | $1,250.00 (Posted) | Matched (Confidence 1.0) |
| **2. Normalized Reference** | `TXN-2026-0006` | $350.00 (Success) | Ref: `TXN 2026 0006` (Spaces) | Matched via Normalization |
| **3. Case Normalization** | `TXN-2026-0007` | $420.00 (Success) | Ref: `txn20260007` (Lowercase) | Matched via Normalization |
| **4. Fee Deduction Mismatch** | `TXN-2026-0002` | $1,000.00 (Success) | $985.00 ($15 discrepancy) | `amount_mismatch` Exception |
| **5. Missing in Bank** | `TXN-2026-0009` | $250.00 (Success) | Not present in bank statement | `missing_in_bank` Exception |
| **6. Missing in Gateway** | `BNK-2026-0012` | Not present in gateway | $75.00 credited | `missing_in_gateway` Exception |
| **7. Duplicate Bank Credit** | `TXN-2026-0011` | $80.00 (1 transaction) | 2 statement entries ($80 each) | `duplicate` Exception |
| **8. Severe Settlement Delay** | `TXN-2026-0010` | 2026-03-01 ($500.00) | Booked 2026-03-07 (+6 days) | `settlement_delay` Exception |
| **9. Critical Status Conflict** | `TXN-2026-0014` | $120.00 (Gateway Success) | Marked "reversed" by bank | Critical Exception & Escalate |
| **10. High-Value Discrepancy** | `TXN-2026-0053` | $15,000.00 (Success) | $14,700.00 ($300 discrepancy) | Critical Severity Exception |

---

## 5–7 Minute Walkthrough Script

### Step 1: Authentication & Dashboard Overview (1:00)
1. Navigate to `http://localhost:5173/login`.
2. Sign in with the **Admin** credentials:
   - Email: `admin@reconcile.ai`
   - Password: `Admin123!`
3. Arrive at `/dashboard`:
   - Point out the **real-time KPI cards** (Total Volume, Reconciled Volume, Pending Exceptions, Match Rate).
   - Show that all figures are derived strictly from database queries without hardcoded dummy values.
   - Highlight the **Reconciliation Health & Status Breakdown** chart and the **Recent Activity Feed**.

### Step 2: Data Ingestion (1:00)
1. Click **Data Import** in the sidebar navigation (`/import`).
2. Demonstrate how financial files are ingested:
   - **Option A (Instant Demo Load)**: As Admin, execute the idempotent demo import via `POST /api/demo/load-sample-data?merchant_id=<id>`. All 53 gateway transactions, 54 bank entries, and 6 settlement records are ingested instantly.
   - **Option B (Drag & Drop UI)**: Select Merchant, select Gateway (Stripe/Razorpay), and drop `data/sample/gateway_transactions.csv`. Repeat for `data/sample/bank_transactions.csv`.
3. Note that the system automatically deduplicates and normalizes incoming records.

### Step 3: Running Deterministic Reconciliation (1:00)
1. Navigate to **Reconciliation** (`/reconciliation`).
2. Select the demo merchant (e.g., *Apex Retail Global*).
3. Click **"Run Reconciliation"**:
   - Explain the **3-tier matching hierarchy**:
     - *Tier 1*: Exact reference match.
     - *Tier 2*: Normalized alphanumeric reference match (handles stripped dashes, spaces, and case variances).
     - *Tier 3*: Amount + transaction date tolerance window fallback.
4. Review the generated reconciliation summary:
   - Notice the high-accuracy matched pairs.
   - Notice that the engine **never uses an LLM** to make matching decisions; matching is 100% deterministic and auditable.

### Step 4: Exception Inspection & 360° View (1:00)
1. Navigate to **Exceptions** (`/exceptions`).
2. Point out the **Workflow Metrics Strip** (Total Exceptions, Open, Investigating, Resolved, Critical).
3. Filter by **Critical Severity** to show `TXN-2026-0014` (Status Mismatch) and `TXN-2026-0053` (High-Value Variance).
4. Click on an exception (e.g., `TXN-2026-0002` - $15 variance) to open the **360° Slide-out Inspector**:
   - Compare Gateway Record ($1,000.00) vs Bank Statement ($985.00).
   - View the calculated delta (-$15.00).

### Step 5: AI Diagnostic Analysis & Autonomous Agent (1:30)
1. From the Slide-out Inspector or the **AI Analysis** tab (`/ai-analysis`), click **"Analyze with AI"**:
   - Point out that the AI operates as an **advisory copilot only**. It explains root causes (e.g., "1.5% interchange fee deduction by processing partner") and assigns a confidence score.
   - Note the **deterministic fallback guarantee**: if the external LLM key is absent or times out, a local rule-based analyzer generates the diagnostic explanation without failing.
2. Switch to **Agent Investigation** (`/agent-investigation`):
   - Launch an autonomous investigation on a complex exception.
   - Watch the agent assemble multi-ledger evidence from 6 distinct sources (Gateway, Bank, Settlement, Audit Log, AI History, Merchant Profile).
   - Review the agent's synthesized decision: `MONITOR`, `REVIEW`, or `ESCALATE`.
   - Show the drafted team escalation ticket routed to `Finance Operations`.

### Step 6: Human-in-the-Loop Review & Resolution (1:00)
1. Return to the exception ticket in `/exceptions`:
2. **Assign Operator**:
   - Assign the ticket to `finance@reconcile.ai`.
   - Status automatically shifts from `open` to `investigating`.
3. **Add Operator Note**:
   - Add a progress note: `"Confirmed $15 fee aligns with international card processing surcharge."`
4. **Resolve Exception**:
   - Click **"Resolve Exception"**.
   - Input resolution note: `"Ledger fee adjustment booked. Account balanced."`
   - Show that an empty note returns a 422 error — resolution notes are mandatory for compliance.
   - Status transitions to terminal `resolved`.
5. **Demonstrate Terminal Protection**:
   - Show that resolved exceptions cannot be modified without supervisor reopening.

### Step 7: Grounded Audit Timeline & Compliance (0:30)
1. In the 360° Inspector, scroll to the **Chronological Audit Timeline**:
   - Review the complete lifecycle: Exception Created → AI Diagnosed → Agent Investigated → Operator Assigned → Note Added → Exception Resolved.
   - Emphasize that all actions are backed by immutable rows in `audit_logs` with timestamps and user identifiers.
2. Conclude the demonstration.

---

## Quick API Verification Cheatsheet

For CLI or Postman verification:

```bash
# 1. Check Service Health
curl http://localhost:8000/api/health

# 2. Login as Admin
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@reconcile.ai","password":"Admin123!"}'

# 3. Load Sample Data (Idempotent)
curl -X POST "http://localhost:8000/api/demo/load-sample-data?merchant_id=<MERCHANT_ID>" \
  -H "Authorization: Bearer <TOKEN>"

# 4. Trigger Reconciliation
curl -X POST http://localhost:8000/api/reconciliation/run \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"merchant_id":"<MERCHANT_ID>"}'
```
