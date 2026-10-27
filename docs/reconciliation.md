# Core Reconciliation Engine Documentation

The **AI-Powered Payment Reconciliation Engine** performs deterministic, auditable matching between Payment Gateway transactions (`transactions` table) and Bank Statement records (`bank_transactions` table).

---

## 1. Architectural Overview

```
API Route (POST /api/reconciliation/run)
  │
  ▼
Pydantic Request Schema
  │
  ▼
ReconciliationService (idempotency, DB transactions, summary aggregation)
  │
  ├── DuplicateDetector (in-file & database reference duplicates)
  ├── ReconciliationEngine (pure computational comparison)
  │     ├── Level 1: Exact Reference Match
  │     ├── Level 2: Normalized Reference Match
  │     └── Level 3: Amount + Date Fallback Match
  │
  ├── ResultBuilder (builds ReconciliationResult & PaymentException ORM records)
  └── Database (PostgreSQL / SQLite in-memory for testing)
```

---

## 2. Deterministic Matching Hierarchy

Matching runs sequentially in the following priority order. Once a transaction pair is matched, both transactions are consumed and removed from subsequent matching tiers.

### Level 1: Exact Reference Match
- **Criteria**: `gateway.transaction_reference == bank.transaction_reference` OR `gateway.transaction_reference == bank.bank_reference`.
- **Status Checks**:
  - If amounts match and no settlement delay: `match_status = "matched"`, `confidence_score = 1.0000`, `matching_method = "exact_reference"`.
  - If amounts differ: `match_status = "amount_mismatch"`, `confidence_score = 0.9000`.
  - If gateway indicates `success` while bank indicates `failed` / `reversed`: `match_status = "unresolved"`, `confidence_score = 0.3000` (critical exception created).

### Level 2: Normalized Reference Match
- **Criteria**: Sanitized references match after stripping formatting.
- **Normalization Rules**:
  1. Converts string to uppercase.
  2. Strips spaces, dashes (`-`), underscores (`_`), and non-alphanumeric symbols.
  3. Example: `TXN-001` → `TXN001`, `txn_001` → `TXN001`.
- Original references in the database are preserved unchanged.
- **Outcome**: `match_status = "matched"`, `confidence_score = 0.9500`, `matching_method = "normalized_reference"`.

### Level 3: Amount + Date Fallback Match
- **Criteria**: For remaining unmatched transactions without reference matches, searches for available bank records where:
  - `bank.amount == gateway.amount`
  - `|bank.transaction_date - gateway.transaction_date| <= 1 day`
- **Ambiguity Guard**:
  - If **exactly 1 candidate** exists: `match_status = "matched"`, `confidence_score = 0.8000`, `matching_method = "amount_date_fallback"`.
  - If **multiple candidates** exist: Marked as `match_status = "unresolved"`, `confidence_score = 0.3000`, explanation `"Multiple candidate bank transactions found for the same amount and date range."`. The engine will **never** arbitrarily choose a candidate.

---

## 3. Anomaly & Discrepancy Detection

### Amount Mismatch
- When references match but monetary amounts differ.
- `expected_amount = gateway.amount`
- `actual_amount = bank.amount`
- `difference_amount = bank.amount - gateway.amount`
- Creates a `PaymentException` with category `"amount_mismatch"`, severity `"high"`.

### Missing in Bank
- Gateway recorded a successful payment, but no matching credit appears in the bank statement.
- `match_status = "missing_in_bank"`
- `difference_amount = -gateway.amount`
- Creates a `PaymentException` with category `"missing_transaction"`, severity `"high"`.

### Missing in Gateway
- Bank statement contains a deposit without an originating gateway transaction.
- `match_status = "missing_in_gateway"`
- `difference_amount = bank.amount`
- Creates a `PaymentException` with category `"missing_transaction"`, severity `"high"`.

### Duplicates
- Detects duplicate references within the file or across database records.
- `match_status = "duplicate"`, `confidence_score = 0.0000`.
- Creates a `PaymentException` with category `"duplicate_transaction"`, severity `"high"`.

### Settlement Delays
- Compares `gateway.transaction_date` against `bank.transaction_date`.
- If `delay > 1 day`: Marked as `exact_reference_delayed` (confidence `0.8500`), retaining `match_status = "matched"`.
- If `delay > 3 days`: Severe delay; creates a `PaymentException` with category `"settlement_delay"`, severity `"medium"`.

### Status Mismatch (Gateway Success vs Bank Failure)
- Gateway indicates payment was charged, but bank records status as `failed` or `reversed`.
- `match_status = "unresolved"`.
- Creates a `PaymentException` with category `"status_mismatch"`, severity `"critical"`.

---

## 4. Deterministic Confidence Scoring

Scores are strictly bounded within `[0.0000, 1.0000]`:

| Scenario | Matching Method | Confidence Score |
| :--- | :--- | :--- |
| Exact reference + exact amount | `exact_reference` | `1.0000` |
| Normalized reference + exact amount | `normalized_reference` | `0.9500` |
| Reference matched + amount mismatch | `exact_reference` | `0.9000` |
| Normalized reference + amount mismatch | `normalized_reference` | `0.8800` |
| Delayed reference match (> 1 day) | `exact_reference_delayed` | `0.8500` |
| Delayed normalized reference match | `normalized_reference_delayed` | `0.8200` |
| Unique Amount + Date fallback match | `amount_date_fallback` | `0.8000` |
| Multiple candidate fallback (unresolved) | `amount_date_fallback` | `0.3000` |
| Status conflict (gateway success, bank fail) | — | `0.3000` |
| Missing in bank / Missing in gateway | `no_bank_match` / `no_gateway_match` | `0.0000` |
| Duplicate transaction | `duplicate` | `0.0000` |

---

## 5. Idempotency Guarantees

Running the reconciliation pipeline repeatedly against the same data is safe:
1. **Reconciliation Results**: The engine checks whether a `ReconciliationResult` already exists for the transaction pair and updates the existing record rather than creating a duplicate.
2. **Exceptions**: Before generating a `PaymentException`, the service checks whether an unresolved (`open` or `investigating`) exception with the same category already exists for that reconciliation record.

---

## 6. API Endpoints

### 1. Trigger Reconciliation Run
```http
POST /api/reconciliation/run
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "merchant_id": "00000000-0000-0000-0000-000000000001"
}
```

**Response**:
```json
{
  "status": "completed",
  "summary": {
    "total_gateway_transactions": 52,
    "total_bank_transactions": 52,
    "matched": 46,
    "partial_match": 0,
    "amount_mismatch": 2,
    "missing_in_bank": 2,
    "missing_in_gateway": 2,
    "duplicates": 0,
    "unresolved": 0,
    "delayed": 3,
    "total_expected_amount": "14250.0000",
    "total_actual_amount": "14180.0000",
    "total_difference": "-70.0000",
    "reconciliation_accuracy": 88.46
  }
}
```

### 2. Query Reconciliation Results
```http
GET /api/reconciliation/results?page=1&page_size=20&match_status=amount_mismatch
Authorization: Bearer <jwt_token>
```

### 3. Get Result Details
```http
GET /api/reconciliation/results/{id}
Authorization: Bearer <jwt_token>
```

### 4. Get Merchant Summary
```http
GET /api/reconciliation/summary/{merchant_id}
Authorization: Bearer <jwt_token>
```
