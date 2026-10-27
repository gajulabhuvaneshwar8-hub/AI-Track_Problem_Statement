"""
tests/test_end_to_end_workflow.py

Comprehensive End-to-End Workflow Validation Test Suite for Step 10:
Covers the complete financial lifecycle:
Upload / Seed -> Reconcile -> Exceptions -> AI Analysis -> Agent Investigation
-> Evidence -> Recommendation -> Human Review -> Lifecycle (Assign/Review/Escalate/Resolve/Ignore)
-> Timeline & Audit Trail -> Idempotency & Merchant Isolation.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from unittest.mock import patch

from app.core.security import hash_password
from app.models.bank_transaction import BankTransaction
from app.models.enums import (
    ExceptionSeverity,
    ExceptionStatus,
    MatchStatus,
    TransactionSource,
    TransactionStatus,
    UserRole,
)
from app.models.exception import PaymentException
from app.models.merchant import Merchant
from app.models.reconciliation_result import ReconciliationResult
from app.models.transaction import Transaction
from app.models.user import User


@pytest.fixture
def test_merchant(db_session):
    merchant = Merchant(
        id=uuid.uuid4(),
        name="Apex Payments Merchant",
        email=f"apex_{uuid.uuid4().hex[:8]}@example.com",
        business_name="Apex Commerce LLC",
    )
    db_session.add(merchant)
    db_session.commit()
    db_session.refresh(merchant)
    return merchant


@pytest.fixture
def second_merchant(db_session):
    merchant = Merchant(
        id=uuid.uuid4(),
        name="Other Merchant",
        email=f"other_{uuid.uuid4().hex[:8]}@example.com",
        business_name="Other Retail LLC",
    )
    db_session.add(merchant)
    db_session.commit()
    db_session.refresh(merchant)
    return merchant


@pytest.fixture
def finance_operator(db_session):
    user = User(
        id=uuid.uuid4(),
        name="Alex Finance",
        email=f"alex_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("SecurePass123!"),
        role=UserRole.finance_user,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def finance_headers(client, finance_operator):
    resp = client.post(
        "/api/auth/login",
        json={"email": finance_operator.email, "password": "SecurePass123!"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestEndToEndWorkflow:
    """End-to-end integration and workflow validation test suite."""

    # 1. Complete successful workflow
    def test_e2e_successful_match_workflow(self, client, auth_headers, test_merchant, db_session):
        now = datetime.now(timezone.utc)
        gtxn = Transaction(
            transaction_reference="E2E-SUCCESS-001",
            merchant_id=test_merchant.id,
            amount=Decimal("250.00"),
            currency="USD",
            transaction_date=now,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        btxn = BankTransaction(
            bank_reference="BNK-SUCCESS-001",
            transaction_reference="E2E-SUCCESS-001",
            amount=Decimal("250.00"),
            transaction_date=now,
            status="posted",
        )
        db_session.add_all([gtxn, btxn])
        db_session.commit()

        # Run reconciliation
        recon_resp = client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(test_merchant.id)},
            headers=auth_headers,
        )
        assert recon_resp.status_code == 200
        summary = recon_resp.json()["summary"]
        assert summary["matched"] >= 1
        assert summary["amount_mismatch"] == 0

        # Verify matched results
        res_list = client.get(
            "/api/reconciliation/results",
            headers=auth_headers,
        )
        assert res_list.status_code == 200
        items = res_list.json()["items"]
        matched_items = [i for i in items if i["transaction_id"] == str(gtxn.id)]
        assert len(matched_items) == 1
        assert matched_items[0]["match_status"] == "matched"

    # 2. Amount mismatch complete workflow: Reconcile -> Exception -> AI -> Agent -> Human Resolve
    @pytest.mark.asyncio
    async def test_e2e_amount_mismatch_complete_workflow(
        self, client, auth_headers, finance_headers, test_merchant, finance_operator, db_session
    ):
        now = datetime.now(timezone.utc)
        gtxn = Transaction(
            transaction_reference="E2E-MISMATCH-001",
            merchant_id=test_merchant.id,
            amount=Decimal("500.00"),
            currency="USD",
            transaction_date=now,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        btxn = BankTransaction(
            bank_reference="BNK-MISMATCH-001",
            transaction_reference="E2E-MISMATCH-001",
            amount=Decimal("485.00"),
            transaction_date=now,
            status="posted",
        )
        db_session.add_all([gtxn, btxn])
        db_session.commit()

        # 1. Run reconciliation
        resp = client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(test_merchant.id)},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["summary"]["amount_mismatch"] >= 1

        # 2. Locate created exception
        exc_resp = client.get("/api/exceptions", headers=auth_headers)
        assert exc_resp.status_code == 200
        exceptions = exc_resp.json()["items"]
        mismatch_exc = next(
            e for e in exceptions if "E2E-MISMATCH-001" in e["title"]
        )
        exc_id = mismatch_exc["id"]
        recon_id = mismatch_exc["reconciliation_id"]

        # 3. AI Analysis
        ai_resp = client.post(
            f"/api/ai/analyze/{recon_id}",
            headers=auth_headers,
        )
        assert ai_resp.status_code == 200
        ai_data = ai_resp.json()
        assert ai_data["reconciliation_id"] == recon_id
        assert ai_data["root_cause"] is not None
        assert float(ai_data["confidence_score"]) > 0

        # 4. Agent Investigation
        agent_resp = client.post(
            f"/api/agents/investigate/{exc_id}",
            headers=auth_headers,
        )
        assert agent_resp.status_code == 200
        agent_data = agent_resp.json()
        assert agent_data["exception_id"] == exc_id
        assert len(agent_data["evidence"]) > 0
        assert agent_data["recommended_action"] is not None

        # 5. Human Review: Assign to finance operator
        assign_resp = client.post(
            f"/api/exceptions/{exc_id}/assign",
            json={"assigned_to": str(finance_operator.id)},
            headers=auth_headers,
        )
        assert assign_resp.status_code == 200
        assert assign_resp.json()["assigned_to"] == str(finance_operator.id)

        # 6. Human Review: Add review note
        review_resp = client.post(
            f"/api/exceptions/{exc_id}/review",
            json={"note": "Verified $15 discrepancy matches standard partner processing fee."},
            headers=finance_headers,
        )
        assert review_resp.status_code == 200
        assert "Verified $15 discrepancy matches standard partner processing fee." in review_resp.json()["reviewer_note"]

        # 7. Resolution: Resolve exception with note
        resolve_resp = client.post(
            f"/api/exceptions/{exc_id}/resolve",
            json={"resolution_note": "Fee deduction ledger adjusted. Transaction fully reconciled."},
            headers=finance_headers,
        )
        assert resolve_resp.status_code == 200
        assert resolve_resp.json()["status"] == "resolved"

    # 3. Missing in bank workflow
    def test_e2e_missing_in_bank_workflow(self, client, auth_headers, test_merchant, db_session):
        now = datetime.now(timezone.utc)
        gtxn = Transaction(
            transaction_reference="E2E-MISSING-BANK-001",
            merchant_id=test_merchant.id,
            amount=Decimal("320.00"),
            currency="USD",
            transaction_date=now,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        db_session.add(gtxn)
        db_session.commit()

        resp = client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(test_merchant.id)},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["summary"]["missing_in_bank"] >= 1

        exc_resp = client.get("/api/exceptions?category=missing_transaction", headers=auth_headers)
        assert exc_resp.status_code == 200
        items = exc_resp.json()["items"]
        assert any("E2E-MISSING-BANK-001" in item["title"] for item in items)

    # 4. Missing in gateway workflow
    def test_e2e_missing_in_gateway_workflow(self, client, auth_headers, test_merchant, db_session):
        now = datetime.now(timezone.utc)
        btxn = BankTransaction(
            bank_reference="BNK-UNMATCHED-999",
            transaction_reference="UNKNOWN-GATEWAY-REF",
            amount=Decimal("1200.00"),
            transaction_date=now,
            status="posted",
        )
        db_session.add(btxn)
        db_session.commit()

        resp = client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(test_merchant.id)},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["summary"]["missing_in_gateway"] >= 1

    # 5. Duplicate transaction workflow
    def test_e2e_duplicate_transaction_workflow(self, client, auth_headers, test_merchant, db_session):
        now = datetime.now(timezone.utc)
        btxn1 = BankTransaction(
            bank_reference="BNK-DUP-100",
            transaction_reference="TXN-DUP-001",
            amount=Decimal("75.00"),
            transaction_date=now,
            status="posted",
        )
        # Same normalized reference with space
        btxn2 = BankTransaction(
            bank_reference="BNK DUP 100",
            transaction_reference="TXN-DUP-001",
            amount=Decimal("75.00"),
            transaction_date=now,
            status="posted",
        )
        db_session.add_all([btxn1, btxn2])
        db_session.commit()

        resp = client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(test_merchant.id)},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["summary"]["duplicates"] >= 1

    # 6. Delayed bank transaction workflow
    def test_e2e_delayed_transaction_workflow(self, client, auth_headers, test_merchant, db_session):
        base_date = datetime.now(timezone.utc) - timedelta(days=7)
        later_date = datetime.now(timezone.utc)

        gtxn = Transaction(
            transaction_reference="E2E-DELAY-001",
            merchant_id=test_merchant.id,
            amount=Decimal("80.00"),
            currency="USD",
            transaction_date=base_date,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        btxn = BankTransaction(
            bank_reference="BNK-DELAY-001",
            transaction_reference="E2E-DELAY-001",
            amount=Decimal("80.00"),
            transaction_date=later_date,
            status="posted",
        )
        db_session.add_all([gtxn, btxn])
        db_session.commit()

        resp = client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(test_merchant.id)},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["summary"]["delayed"] >= 1

    # 7. Critical status mismatch workflow: gateway success vs bank reversed
    def test_e2e_critical_status_mismatch_workflow(self, client, auth_headers, test_merchant, db_session):
        now = datetime.now(timezone.utc)
        gtxn = Transaction(
            transaction_reference="E2E-STATUS-CONFLICT",
            merchant_id=test_merchant.id,
            amount=Decimal("900.00"),
            currency="USD",
            transaction_date=now,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        btxn = BankTransaction(
            bank_reference="BNK-STATUS-CONFLICT",
            transaction_reference="E2E-STATUS-CONFLICT",
            amount=Decimal("900.00"),
            transaction_date=now,
            status="reversed",
            description="REVERSED ACH TRANSACTION",
        )
        db_session.add_all([gtxn, btxn])
        db_session.commit()

        resp = client.post(
            "/api/reconciliation/run",
            json={"merchant_id": str(test_merchant.id)},
            headers=auth_headers,
        )
        assert resp.status_code == 200

        # Verify critical exception created
        exc_resp = client.get("/api/exceptions?severity=critical", headers=auth_headers)
        assert exc_resp.status_code == 200
        crit_items = exc_resp.json()["items"]
        assert any("E2E-STATUS-CONFLICT" in item["title"] for item in crit_items)

    # 8. AI fallback workflow
    @pytest.mark.asyncio
    async def test_e2e_ai_fallback_workflow(self, client, auth_headers, test_merchant, db_session):
        now = datetime.now(timezone.utc)
        gtxn = Transaction(
            transaction_reference="E2E-AIFALLBACK-01",
            merchant_id=test_merchant.id,
            amount=Decimal("150.00"),
            currency="USD",
            transaction_date=now,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        btxn = BankTransaction(
            bank_reference="BNK-AIFALLBACK-01",
            transaction_reference="E2E-AIFALLBACK-01",
            amount=Decimal("145.00"),
            transaction_date=now,
            status="posted",
        )
        db_session.add_all([gtxn, btxn])
        db_session.commit()

        client.post("/api/reconciliation/run", json={"merchant_id": str(test_merchant.id)}, headers=auth_headers)
        recon = db_session.query(ReconciliationResult).filter(
            ReconciliationResult.match_status == MatchStatus.amount_mismatch
        ).first()
        assert recon is not None

        # Force AI client failure to test deterministic fallback
        with patch("app.services.ai.ai_client.AIClient.generate_analysis", side_effect=RuntimeError("AI API Unavailable")):
            resp = client.post(f"/api/ai/analyze/{recon.id}", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "fallback" or data.get("ai_provider") == "deterministic_fallback"
            assert "fee" in data["root_cause"].lower() or "mismatch" in data["root_cause"].lower()

    # 9. Agent fallback workflow
    @pytest.mark.asyncio
    async def test_e2e_agent_fallback_workflow(self, client, auth_headers, test_merchant, db_session):
        now = datetime.now(timezone.utc)
        gtxn = Transaction(
            transaction_reference="E2E-AGENTFALLBACK-01",
            merchant_id=test_merchant.id,
            amount=Decimal("300.00"),
            currency="USD",
            transaction_date=now,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        btxn = BankTransaction(
            bank_reference="BNK-AGENTFALLBACK-01",
            transaction_reference="E2E-AGENTFALLBACK-01",
            amount=Decimal("290.00"),
            transaction_date=now,
            status="posted",
        )
        db_session.add_all([gtxn, btxn])
        db_session.commit()

        client.post("/api/reconciliation/run", json={"merchant_id": str(test_merchant.id)}, headers=auth_headers)
        exc = db_session.query(PaymentException).filter(PaymentException.category == "amount_mismatch").first()
        assert exc is not None

        # Simulate agent tool / LLM failure
        with patch("app.services.ai.ai_client.AIClient.generate_analysis", side_effect=Exception("LLM Timeout")):
            resp = client.post(f"/api/agents/investigate/{exc.id}", headers=auth_headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["exception_id"] == str(exc.id)
            assert data["decision"] in ["monitor", "review", "escalate"]
            assert len(data["evidence"]) > 0

    # 10. Human review workflow
    def test_e2e_human_review_workflow(self, client, auth_headers, finance_headers, test_merchant, finance_operator, db_session):
        exc = PaymentException(
            merchant_id=test_merchant.id,
            severity=ExceptionSeverity.medium,
            category="settlement_delay",
            title="Review Workflow Test Exception",
            description="Testing human review transitions",
            status=ExceptionStatus.open,
        )
        db_session.add(exc)
        db_session.commit()

        # Assign
        resp = client.post(
            f"/api/exceptions/{exc.id}/assign",
            json={"assigned_to": str(finance_operator.id)},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["assigned_to"] == str(finance_operator.id)

        # Review
        rev_resp = client.post(
            f"/api/exceptions/{exc.id}/review",
            json={"note": "Investigating settlement timeline with banking partner."},
            headers=finance_headers,
        )
        assert rev_resp.status_code == 200
        assert "Investigating settlement timeline with banking partner." in rev_resp.json()["reviewer_note"]

    # 11. Escalation workflow
    def test_e2e_escalation_workflow(self, client, finance_headers, test_merchant, db_session):
        exc = PaymentException(
            merchant_id=test_merchant.id,
            severity=ExceptionSeverity.high,
            category="amount_mismatch",
            title="Escalation Test Exception",
            description="Testing escalation reason requirement and audit",
            status=ExceptionStatus.open,
        )
        db_session.add(exc)
        db_session.commit()

        # Missing escalation reason should return 422
        bad_resp = client.post(
            f"/api/exceptions/{exc.id}/escalate",
            json={},
            headers=finance_headers,
        )
        assert bad_resp.status_code == 422

        # Valid escalation
        good_resp = client.post(
            f"/api/exceptions/{exc.id}/escalate",
            json={"reason": "High variance unconfirmed by payment processor."},
            headers=finance_headers,
        )
        assert good_resp.status_code == 200
        assert good_resp.json()["escalation_reason"] == "High variance unconfirmed by payment processor."
        assert good_resp.json()["escalated_at"] is not None

    # 12. Resolution workflow
    def test_e2e_resolution_workflow(self, client, finance_headers, test_merchant, db_session):
        exc = PaymentException(
            merchant_id=test_merchant.id,
            severity=ExceptionSeverity.medium,
            category="settlement_delay",
            title="Resolution Test Exception",
            description="Testing resolution note and audit",
            status=ExceptionStatus.investigating,
        )
        db_session.add(exc)
        db_session.commit()

        # Missing resolution note should return 422
        bad_resp = client.post(
            f"/api/exceptions/{exc.id}/resolve",
            json={},
            headers=finance_headers,
        )
        assert bad_resp.status_code == 422

        # Valid resolution
        good_resp = client.post(
            f"/api/exceptions/{exc.id}/resolve",
            json={"resolution_note": "Funds cleared and verified on bank ledger."},
            headers=finance_headers,
        )
        assert good_resp.status_code == 200
        assert good_resp.json()["status"] == "resolved"

    # 13. Ignore workflow
    def test_e2e_ignore_workflow(self, client, auth_headers, test_merchant, db_session):
        exc = PaymentException(
            merchant_id=test_merchant.id,
            severity=ExceptionSeverity.low,
            category="unresolved_match",
            title="Ignore Test Exception",
            description="Testing ignore note and state transition",
            status=ExceptionStatus.open,
        )
        db_session.add(exc)
        db_session.commit()

        resp = client.post(
            f"/api/exceptions/{exc.id}/ignore",
            json={"reason": "Determined to be an internal non-reconciling test transaction."},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    # 14. Audit timeline workflow
    def test_e2e_audit_timeline_workflow(self, client, auth_headers, test_merchant, finance_operator, db_session):
        exc = PaymentException(
            merchant_id=test_merchant.id,
            severity=ExceptionSeverity.high,
            category="amount_mismatch",
            title="Audit Timeline Test",
            description="Verify timeline history events",
            status=ExceptionStatus.open,
        )
        db_session.add(exc)
        db_session.commit()

        # Assign then resolve
        client.post(
            f"/api/exceptions/{exc.id}/assign",
            json={"assigned_to": str(finance_operator.id)},
            headers=auth_headers,
        )
        client.post(
            f"/api/exceptions/{exc.id}/resolve",
            json={"resolution_note": "Resolved and logged."},
            headers=auth_headers,
        )

        timeline_resp = client.get(f"/api/exceptions/{exc.id}/timeline", headers=auth_headers)
        assert timeline_resp.status_code == 200
        events = timeline_resp.json()["events"]
        assert len(events) >= 2
        actions = [ev["title"].lower() + " " + (ev.get("description") or "").lower() for ev in events]
        assert any("assign" in a for a in actions)
        assert any("resolve" in a for a in actions)

    # 15. Repeated reconciliation idempotency
    def test_e2e_repeated_reconciliation_idempotency(self, client, auth_headers, test_merchant, db_session):
        now = datetime.now(timezone.utc)
        gtxn = Transaction(
            transaction_reference="E2E-IDEMP-001",
            merchant_id=test_merchant.id,
            amount=Decimal("120.00"),
            currency="USD",
            transaction_date=now,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        btxn = BankTransaction(
            bank_reference="BNK-IDEMP-001",
            transaction_reference="E2E-IDEMP-001",
            amount=Decimal("115.00"),  # $5 mismatch -> triggers exception
            transaction_date=now,
            status="posted",
        )
        db_session.add_all([gtxn, btxn])
        db_session.commit()

        # Run 1
        resp1 = client.post("/api/reconciliation/run", json={"merchant_id": str(test_merchant.id)}, headers=auth_headers)
        assert resp1.status_code == 200

        # Count results and exceptions
        res_count_1 = db_session.query(ReconciliationResult).count()
        exc_count_1 = db_session.query(PaymentException).count()

        # Run 2 (repeated)
        resp2 = client.post("/api/reconciliation/run", json={"merchant_id": str(test_merchant.id)}, headers=auth_headers)
        assert resp2.status_code == 200

        res_count_2 = db_session.query(ReconciliationResult).count()
        exc_count_2 = db_session.query(PaymentException).count()

        # Must not duplicate records
        assert res_count_1 == res_count_2
        assert exc_count_1 == exc_count_2

    # 16. Merchant isolation & RBAC
    def test_e2e_merchant_isolation_workflow(self, client, auth_headers, test_merchant, second_merchant, db_session):
        # Create exception belonging to test_merchant
        exc_m1 = PaymentException(
            merchant_id=test_merchant.id,
            severity=ExceptionSeverity.high,
            category="amount_mismatch",
            title="M1 Confidential Exception",
            description="Merchant 1 only",
            status=ExceptionStatus.open,
        )
        # Create exception belonging to second_merchant
        exc_m2 = PaymentException(
            merchant_id=second_merchant.id,
            severity=ExceptionSeverity.medium,
            category="settlement_delay",
            title="M2 Confidential Exception",
            description="Merchant 2 only",
            status=ExceptionStatus.open,
        )
        db_session.add_all([exc_m1, exc_m2])
        db_session.commit()

        # Listing exceptions filtered by test_merchant should only contain M1
        list_resp_m1 = client.get(f"/api/exceptions?merchant_id={test_merchant.id}", headers=auth_headers)
        assert list_resp_m1.status_code == 200
        items_m1 = [e["id"] for e in list_resp_m1.json()["items"]]
        assert str(exc_m1.id) in items_m1
        assert str(exc_m2.id) not in items_m1

        # Listing exceptions filtered by second_merchant should only contain M2
        list_resp_m2 = client.get(f"/api/exceptions?merchant_id={second_merchant.id}", headers=auth_headers)
        assert list_resp_m2.status_code == 200
        items_m2 = [e["id"] for e in list_resp_m2.json()["items"]]
        assert str(exc_m2.id) in items_m2
        assert str(exc_m1.id) not in items_m2

    # 17. Demo sample data endpoint
    def test_e2e_demo_load_sample_data_endpoint(self, client, auth_headers, finance_headers, test_merchant):
        # Finance user should be denied (admin only)
        forbidden_resp = client.post(
            f"/api/demo/load-sample-data?merchant_id={test_merchant.id}",
            headers=finance_headers,
        )
        assert forbidden_resp.status_code == 403

        # Admin user should succeed
        admin_resp = client.post(
            f"/api/demo/load-sample-data?merchant_id={test_merchant.id}",
            headers=auth_headers,
        )
        assert admin_resp.status_code == 200
        data = admin_resp.json()
        assert data["status"] == "success"
        assert data["gateway"]["imported"] > 0
        assert data["bank"]["imported"] > 0
        assert data["settlement"]["imported"] > 0

        # Repeated run should be idempotent (no new records imported)
        repeat_resp = client.post(
            f"/api/demo/load-sample-data?merchant_id={test_merchant.id}",
            headers=auth_headers,
        )
        assert repeat_resp.status_code == 200
        repeat_data = repeat_resp.json()
        assert repeat_data["gateway"]["imported"] == 0
        assert repeat_data["gateway"]["duplicates"] > 0

    # 18. High-value exception workflow
    def test_e2e_high_value_exception_workflow(self, client, auth_headers, test_merchant, db_session):
        now = datetime.now(timezone.utc)
        gtxn = Transaction(
            transaction_reference="E2E-HIGHVALUE-001",
            merchant_id=test_merchant.id,
            amount=Decimal("25000.00"),
            currency="USD",
            transaction_date=now,
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        btxn = BankTransaction(
            bank_reference="BNK-HIGHVALUE-001",
            transaction_reference="E2E-HIGHVALUE-001",
            amount=Decimal("24500.00"),
            transaction_date=now,
            status="posted",
        )
        db_session.add_all([gtxn, btxn])
        db_session.commit()

        resp = client.post("/api/reconciliation/run", json={"merchant_id": str(test_merchant.id)}, headers=auth_headers)
        assert resp.status_code == 200

        exc = db_session.query(PaymentException).filter(
            PaymentException.title.like("%E2E-HIGHVALUE-001%")
        ).first()
        assert exc is not None
        assert exc.severity in [ExceptionSeverity.high, ExceptionSeverity.critical]
