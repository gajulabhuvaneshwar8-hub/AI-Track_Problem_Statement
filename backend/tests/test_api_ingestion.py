"""
tests/test_api_ingestion.py

Comprehensive tests for CSV/Excel data ingestion pipeline:
- Gateway, Bank, and Settlement file uploads
- In-file and DB deduplication
- Column alias mapping and data normalization
- Row validation and error reporting
- File format validation (CSV, XLSX)
- Authentication and merchant scoping
- Batch history pagination and filtering
"""

import io
from decimal import Decimal
import pandas as pd
import pytest

from app.models.enums import ImportSource, ImportStatus
from app.models.import_batch import ImportBatch
from app.models.transaction import Transaction
from app.models.bank_transaction import BankTransaction
from app.models.settlement import Settlement
from app.services.ingestion.csv_reader import CSVReadError, read_csv_bytes
from app.services.ingestion.normalizer import (
    normalize_currency,
    normalize_gateway_status,
    parse_datetime,
    parse_decimal,
)


# ---------------------------------------------------------------------------
# Helpers for building in-memory files
# ---------------------------------------------------------------------------

def create_csv_bytes(content: str) -> bytes:
    """Encode string content to UTF-8 bytes."""
    return content.encode("utf-8")


def create_xlsx_bytes(df: pd.DataFrame) -> bytes:
    """Generate in-memory Excel XLSX bytes from DataFrame."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Unit tests: Normalizer & Readers
# ---------------------------------------------------------------------------

class TestIngestionUnits:
    """Unit tests for reader and normalizer primitives."""

    def test_parse_decimal_clean(self):
        assert parse_decimal("125.50") == Decimal("125.50")
        assert parse_decimal("$1,250.75") == Decimal("1250.75")
        assert parse_decimal(" -45.00 ") == Decimal("-45.00")
        assert parse_decimal("invalid") is None
        assert parse_decimal(None) is None

    def test_parse_datetime_formats(self):
        dt1 = parse_datetime("2026-03-01 10:15:30")
        assert dt1 is not None
        assert dt1.year == 2026 and dt1.month == 3 and dt1.day == 1

        dt2 = parse_datetime("01/03/2026")
        assert dt2 is not None

        assert parse_datetime("not-a-date") is None
        assert parse_datetime(None) is None

    def test_normalize_currency(self):
        assert normalize_currency("usd") == "USD"
        assert normalize_currency(" EUR ") == "EUR"
        assert normalize_currency("") == "USD"
        assert normalize_currency(None) == "USD"

    def test_normalize_gateway_status(self):
        assert normalize_gateway_status("Success") == "success"
        assert normalize_gateway_status("failed") == "failed"
        assert normalize_gateway_status("Processing") == "pending"
        assert normalize_gateway_status("chargeback") == "disputed"

    def test_read_csv_bytes_bom(self):
        content = "\ufefftxn_ref,amount,date\nTXN-01,100,2026-01-01\n"
        df = read_csv_bytes(content.encode("utf-8-sig"))
        assert "txn_ref" in df.columns
        assert len(df) == 1

    def test_read_csv_empty_raises(self):
        with pytest.raises(CSVReadError):
            read_csv_bytes(b"")


# ---------------------------------------------------------------------------
# API tests: Gateway Ingestion
# ---------------------------------------------------------------------------

class TestGatewayIngestionAPI:
    """Tests for POST /api/ingestion/gateway."""

    def test_upload_gateway_csv_success(self, client, auth_headers):
        csv_data = (
            "transaction_reference,order_reference,amount,currency,transaction_date,payment_method,gateway,status\n"
            "TX-TEST-001,ORD-101,150.00,USD,2026-03-01 10:00:00,credit_card,Stripe,success\n"
            "TX-TEST-002,ORD-102,75.50,USD,2026-03-01 11:00:00,paypal,PayPal,success\n"
        )
        files = {"file": ("gateway_data.csv", create_csv_bytes(csv_data), "text/csv")}
        resp = client.post("/api/ingestion/gateway", files=files, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_rows"] == 2
        assert data["imported_rows"] == 2
        assert data["duplicate_rows"] == 0
        assert data["invalid_rows"] == 0
        assert data["status"] == "completed"
        assert len(data["errors"]) == 0

    def test_upload_gateway_csv_with_duplicates(self, client, auth_headers):
        csv_data = (
            "transaction_reference,amount,transaction_date\n"
            "TX-DUP-001,100.00,2026-03-01 10:00:00\n"
            "TX-DUP-001,100.00,2026-03-01 10:00:00\n"
            "TX-DUP-002,200.00,2026-03-01 11:00:00\n"
        )
        files = {"file": ("gateway_dups.csv", create_csv_bytes(csv_data), "text/csv")}
        resp = client.post("/api/ingestion/gateway", files=files, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_rows"] == 3
        assert data["imported_rows"] == 2
        assert data["duplicate_rows"] == 1
        assert data["status"] == "completed_with_errors"
        assert any("Duplicate" in e["error"] for e in data["errors"])

    def test_upload_gateway_csv_invalid_amount(self, client, auth_headers):
        csv_data = (
            "transaction_reference,amount,transaction_date\n"
            "TX-INV-001,-50.00,2026-03-01 10:00:00\n"
            "TX-INV-002,invalid_amt,2026-03-01 11:00:00\n"
            "TX-INV-003,120.00,2026-03-01 12:00:00\n"
        )
        files = {"file": ("gateway_invalid.csv", create_csv_bytes(csv_data), "text/csv")}
        resp = client.post("/api/ingestion/gateway", files=files, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_rows"] == 3
        assert data["imported_rows"] == 1
        assert data["invalid_rows"] == 2
        assert data["status"] == "completed_with_errors"

    def test_upload_gateway_missing_ref_column(self, client, auth_headers):
        csv_data = (
            "customer_name,amount,transaction_date\n"
            "Alice,100.00,2026-03-01 10:00:00\n"
        )
        files = {"file": ("gateway_no_ref.csv", create_csv_bytes(csv_data), "text/csv")}
        resp = client.post("/api/ingestion/gateway", files=files, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["imported_rows"] == 0
        assert data["status"] == "failed"
        assert "transaction_reference" in data["errors"][0]["error"]

    def test_upload_gateway_unsupported_format(self, client, auth_headers):
        files = {"file": ("data.txt", b"plain text", "text/plain")}
        resp = client.post("/api/ingestion/gateway", files=files, headers=auth_headers)
        assert resp.status_code == 400
        assert "Unsupported file format" in resp.json()["detail"]

    def test_upload_gateway_xlsx_success(self, client, auth_headers):
        df = pd.DataFrame([
            {"transaction_reference": "TX-XLSX-01", "amount": "99.99", "transaction_date": "2026-03-01 10:00:00"},
            {"transaction_reference": "TX-XLSX-02", "amount": "149.50", "transaction_date": "2026-03-01 11:00:00"},
        ])
        xlsx_bytes = create_xlsx_bytes(df)
        files = {"file": ("gateway.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        resp = client.post("/api/ingestion/gateway", files=files, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["imported_rows"] == 2
        assert data["status"] == "completed"


# ---------------------------------------------------------------------------
# API tests: Bank Ingestion
# ---------------------------------------------------------------------------

class TestBankIngestionAPI:
    """Tests for POST /api/ingestion/bank."""

    def test_upload_bank_csv_success(self, client, auth_headers):
        csv_data = (
            "bank_reference,transaction_reference,amount,currency,booking_date,description,bank_name\n"
            "BNK-TEST-001,TX-REF-001,150.00,USD,2026-03-01 14:00:00,STRIPE SETTLEMENT,Chase Bank\n"
            "BNK-TEST-002,,2500.00,USD,2026-03-01 15:00:00,WIRE TRANSFER,Chase Bank\n"
        )
        files = {"file": ("bank_statement.csv", create_csv_bytes(csv_data), "text/csv")}
        resp = client.post("/api/ingestion/bank", files=files, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_rows"] == 2
        assert data["imported_rows"] == 2
        assert data["status"] == "completed"

    def test_upload_bank_duplicate_rejected(self, client, auth_headers):
        csv_data = (
            "bank_reference,amount,booking_date\n"
            "BNK-DUP-01,100.00,2026-03-01 10:00:00\n"
            "BNK-DUP-01,100.00,2026-03-01 10:00:00\n"
        )
        files = {"file": ("bank_dups.csv", create_csv_bytes(csv_data), "text/csv")}
        resp = client.post("/api/ingestion/bank", files=files, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["imported_rows"] == 1
        assert data["duplicate_rows"] == 1

    def test_upload_bank_xlsx_success(self, client, auth_headers):
        df = pd.DataFrame([
            {"bank_reference": "BNK-XLSX-01", "amount": "400.00", "booking_date": "2026-03-01 12:00:00"},
        ])
        xlsx_bytes = create_xlsx_bytes(df)
        files = {"file": ("bank.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        resp = client.post("/api/ingestion/bank", files=files, headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json()["imported_rows"] == 1


# ---------------------------------------------------------------------------
# API tests: Settlement Ingestion
# ---------------------------------------------------------------------------

class TestSettlementIngestionAPI:
    """Tests for POST /api/ingestion/settlement."""

    def test_upload_settlement_csv_success(self, client, auth_headers):
        csv_data = (
            "settlement_reference,settlement_date,gross_amount,fees,net_amount,currency,status\n"
            "STL-TEST-001,2026-03-01 23:59:59,1000.00,30.00,970.00,USD,settled\n"
            "STL-TEST-002,2026-03-02 23:59:59,500.00,15.00,485.00,USD,settled\n"
        )
        files = {"file": ("settlements.csv", create_csv_bytes(csv_data), "text/csv")}
        resp = client.post("/api/ingestion/settlement", files=files, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_rows"] == 2
        assert data["imported_rows"] == 2
        assert data["status"] == "completed"

    def test_upload_settlement_duplicate(self, client, auth_headers):
        csv_data = (
            "settlement_reference,settlement_date,gross_amount,net_amount\n"
            "STL-DUP-01,2026-03-01 23:59:59,1000.00,970.00\n"
            "STL-DUP-01,2026-03-01 23:59:59,1000.00,970.00\n"
        )
        files = {"file": ("settle_dups.csv", create_csv_bytes(csv_data), "text/csv")}
        resp = client.post("/api/ingestion/settlement", files=files, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["imported_rows"] == 1
        assert data["duplicate_rows"] == 1


# ---------------------------------------------------------------------------
# API tests: Security & History
# ---------------------------------------------------------------------------

class TestSecurityAndHistoryAPI:
    """Tests for auth checks, merchant validation, and batch history query."""

    def test_upload_unauthenticated_returns_401(self, client):
        csv_data = "transaction_reference,amount,transaction_date\nTX-01,100,2026-01-01\n"
        files = {"file": ("data.csv", create_csv_bytes(csv_data), "text/csv")}
        resp = client.post("/api/ingestion/gateway", files=files)
        assert resp.status_code == 401

    def test_upload_invalid_merchant_id_returns_404(self, client, auth_headers):
        csv_data = "transaction_reference,amount,transaction_date\nTX-01,100,2026-01-01\n"
        files = {"file": ("data.csv", create_csv_bytes(csv_data), "text/csv")}
        data = {"merchant_id": "00000000-0000-0000-0000-000000000099"}
        resp = client.post("/api/ingestion/gateway", files=files, data=data, headers=auth_headers)
        assert resp.status_code == 404

    def test_get_import_history_paginated(self, client, auth_headers):
        # Upload a batch first
        csv_data = "transaction_reference,amount,transaction_date\nTX-HIST-01,50.00,2026-03-01 10:00:00\n"
        files = {"file": ("hist_test.csv", create_csv_bytes(csv_data), "text/csv")}
        client.post("/api/ingestion/gateway", files=files, headers=auth_headers)

        resp = client.get("/api/ingestion/history?page=1&page_size=10", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] >= 1
        assert any(item["file_name"] == "hist_test.csv" for item in data["items"])

    def test_get_import_history_filtered_by_source(self, client, auth_headers):
        resp = client.get("/api/ingestion/history?source=gateway", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["source"] == "gateway" for item in data["items"])
