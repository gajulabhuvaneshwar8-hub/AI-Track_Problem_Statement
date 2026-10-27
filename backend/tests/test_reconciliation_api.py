"""
tests/test_reconciliation_api.py

API integration tests for reconciliation routes:
- POST /api/reconciliation/run
- GET /api/reconciliation/results
- GET /api/reconciliation/results/{id}
- GET /api/reconciliation/summary/{merchant_id}
- Idempotency & exception tracking
- Role-based authentication
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.bank_transaction import BankTransaction
from app.models.enums import TransactionSource, TransactionStatus
from app.models.exception import PaymentException
from app.models.merchant import Merchant
from app.models.reconciliation_result import ReconciliationResult
from app.models.transaction import Transaction


def _seed_merchant(db: Session, email_suffix: str = "1") -> Merchant:
    """Helper to seed a test merchant."""
    merchant = Merchant(
        name=f"Test Merchant {email_suffix}",
        email=f"merchant_{email_suffix}_{uuid.uuid4().hex[:6]}@example.com",
        business_name=f"Merchant Corp {email_suffix}",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


class TestReconciliationAPI:
    """Integration tests for reconciliation endpoints."""

    def test_run_reconciliation_unauthenticated_returns_401(self, client):
        resp = client.post("/api/reconciliation/run", json={})
        assert resp.status_code == 401

    def test_run_reconciliation_empty_returns_completed(self, client, auth_headers):
        resp = client.post("/api/reconciliation/run", json={}, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["summary"]["total_gateway_transactions"] == 0
        assert data["summary"]["matched"] == 0

    def test_run_reconciliation_with_exact_match(self, client, auth_headers, db_session):
        merchant = _seed_merchant(db_session, "exact")

        now = datetime.now(timezone.utc)
        gtxn = Transaction(
            transaction_reference="TXN-API-001",
            merchant_id=merchant.id,
            amount=Decimal("150.00"),
            currency="USD",
            transaction_date=now,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        btxn = BankTransaction(
            bank_reference="BNK-API-001",
            transaction_reference="TXN-API-001",
            amount=Decimal("150.00"),
            transaction_date=now,
            status="posted",
        )
        db_session.add_all([gtxn, btxn])
        db_session.commit()

        resp = client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(merchant.id)},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        summary = resp.json()["summary"]
        assert summary["total_gateway_transactions"] == 1
        assert summary["matched"] == 1
        assert summary["reconciliation_accuracy"] == 100.0

    def test_reconciliation_idempotency(self, client, auth_headers, db_session):
        merchant = _seed_merchant(db_session, "idempotent")

        now = datetime.now(timezone.utc)
        gtxn = Transaction(
            transaction_reference="TXN-IDEMP-001",
            merchant_id=merchant.id,
            amount=Decimal("300.00"),
            currency="USD",
            transaction_date=now,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        btxn = BankTransaction(
            bank_reference="BNK-IDEMP-001",
            transaction_reference="TXN-IDEMP-001",
            amount=Decimal("300.00"),
            transaction_date=now,
            status="posted",
        )
        db_session.add_all([gtxn, btxn])
        db_session.commit()

        # Run 1
        resp1 = client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(merchant.id)},
            headers=auth_headers,
        )
        assert resp1.status_code == 200

        results_count_1 = db_session.query(ReconciliationResult).count()

        # Run 2 on unchanged data
        resp2 = client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(merchant.id)},
            headers=auth_headers,
        )
        assert resp2.status_code == 200

        results_count_2 = db_session.query(ReconciliationResult).count()
        # Must be exactly the same count — no duplicates created!
        assert results_count_1 == results_count_2

    def test_exception_generation_and_deduplication(self, client, auth_headers, db_session):
        merchant = _seed_merchant(db_session, "exc")

        now = datetime.now(timezone.utc)
        # Mismatched amount: gateway 500, bank 450
        gtxn = Transaction(
            transaction_reference="TXN-MISMATCH-01",
            merchant_id=merchant.id,
            amount=Decimal("500.00"),
            currency="USD",
            transaction_date=now,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        btxn = BankTransaction(
            bank_reference="BNK-MISMATCH-01",
            transaction_reference="TXN-MISMATCH-01",
            amount=Decimal("450.00"),
            transaction_date=now,
            status="posted",
        )
        db_session.add_all([gtxn, btxn])
        db_session.commit()

        # First run generates exception
        resp = client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(merchant.id)},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["summary"]["amount_mismatch"] == 1

        exc_count_1 = db_session.query(PaymentException).count()
        assert exc_count_1 >= 1

        # Second run should NOT duplicate the open exception
        client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(merchant.id)},
            headers=auth_headers,
        )
        exc_count_2 = db_session.query(PaymentException).count()
        assert exc_count_1 == exc_count_2

    def test_list_reconciliation_results(self, client, auth_headers):
        resp = client.get("/api/reconciliation/results?page=1&page_size=10", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_filter_results_by_match_status(self, client, auth_headers):
        resp = client.get("/api/reconciliation/results?match_status=matched", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["match_status"] == "matched" for item in data["items"])

    def test_get_reconciliation_result_by_id(self, client, auth_headers, db_session):
        # Seed a dummy result
        result = ReconciliationResult(
            match_status="matched",
            confidence_score=Decimal("1.0000"),
            expected_amount=Decimal("100.00"),
            actual_amount=Decimal("100.00"),
            difference_amount=Decimal("0.0000"),
            matching_method="exact_reference",
            explanation="Exact match",
            reconciled_at=datetime.now(timezone.utc),
        )
        db_session.add(result)
        db_session.commit()
        db_session.refresh(result)

        resp = client.get(f"/api/reconciliation/results/{result.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(result.id)
        assert data["matching_method"] == "exact_reference"

    def test_get_reconciliation_result_not_found(self, client, auth_headers):
        unknown_id = uuid.uuid4()
        resp = client.get(f"/api/reconciliation/results/{unknown_id}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_reconciliation_summary_endpoint(self, client, auth_headers, db_session):
        merchant = _seed_merchant(db_session, "summary")
        resp = client.get(f"/api/reconciliation/summary/{merchant.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_gateway_transactions" in data
        assert "reconciliation_accuracy" in data
