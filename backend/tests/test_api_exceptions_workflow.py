"""
tests/test_api_exceptions_workflow.py

Comprehensive test suite for Step 9: Exception Management & Human-in-the-Loop Workflow.
Verifies all workflow transitions, validations, role checks, audit logs, timelines,
and detailed evidence projections.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
import pytest

from app.models.enums import (
    AnalysisType,
    ExceptionSeverity,
    ExceptionStatus,
    MatchStatus,
    RiskLevel,
    TransactionStatus,
    UserRole,
)
from app.models.exception import PaymentException
from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.models.bank_transaction import BankTransaction
from app.models.reconciliation_result import ReconciliationResult
from app.models.ai_analysis import AIAnalysis
from app.models.audit_log import AuditLog
from app.models.user import User
from app.core.security import hash_password


@pytest.fixture
def sample_merchant(db_session):
    merchant = Merchant(
        id=uuid.uuid4(),
        name="Global Acme Corp",
        email=f"acme_{uuid.uuid4().hex[:8]}@example.com",
        business_name="Acme Corporation",
    )
    db_session.add(merchant)
    db_session.commit()
    db_session.refresh(merchant)
    return merchant


@pytest.fixture
def test_operator_user(db_session):
    user = User(
        id=uuid.uuid4(),
        name="Sarah Ops",
        email=f"sarah_{uuid.uuid4().hex[:8]}@example.com",
        password_hash=hash_password("OperatorPass123!"),
        role=UserRole.finance_user,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def active_exception(client, auth_headers, sample_merchant):
    resp = client.post(
        "/api/exceptions",
        json={
            "severity": "high",
            "category": "amount_mismatch",
            "title": "Gateway mismatch of 50.00 INR",
            "description": "Internal transaction recorded 1050.00 but bank has 1000.00",
            "status": "open",
            "merchant_id": str(sample_merchant.id),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# 1. Summary & Assignees Tests
# ---------------------------------------------------------------------------


def test_workflow_summary_counts(client, auth_headers, active_exception):
    resp = client.get("/api/exceptions/workflow-summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "open" in data
    assert "investigating" in data
    assert "resolved" in data
    assert "ignored" in data
    assert "escalated" in data
    assert data["total"] >= 1
    assert data["open"] >= 1


def test_workflow_summary_with_merchant_filter(client, auth_headers, active_exception, sample_merchant):
    resp = client.get(
        f"/api/exceptions/workflow-summary?merchant_id={sample_merchant.id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1

    # Filter with non-existent merchant
    empty_merchant_id = uuid.uuid4()
    resp_empty = client.get(
        f"/api/exceptions/workflow-summary?merchant_id={empty_merchant_id}",
        headers=auth_headers,
    )
    assert resp_empty.status_code == 200
    assert resp_empty.json()["total"] == 0


def test_list_assignees(client, auth_headers, test_operator_user):
    resp = client.get("/api/exceptions/assignees", headers=auth_headers)
    assert resp.status_code == 200
    users = resp.json()
    assert isinstance(users, list)
    assert len(users) >= 1
    assert any(u["id"] == str(test_operator_user.id) for u in users)


# ---------------------------------------------------------------------------
# 2. Assignment Tests
# ---------------------------------------------------------------------------


def test_assign_exception_success(client, auth_headers, active_exception, test_operator_user, db_session):
    exc_id = active_exception["id"]
    resp = client.post(
        f"/api/exceptions/{exc_id}/assign",
        json={"assigned_to": str(test_operator_user.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["assigned_to"] == str(test_operator_user.id)
    assert data["assignee_name"] == test_operator_user.name

    # Check audit log
    log = db_session.query(AuditLog).filter(
        AuditLog.entity_id == exc_id,
        AuditLog.action == "exception_assigned",
    ).first()
    assert log is not None
    assert log.details["assigned_to"] == str(test_operator_user.id)


def test_unassign_exception_success(client, auth_headers, active_exception, test_operator_user):
    exc_id = active_exception["id"]
    # First assign
    client.post(
        f"/api/exceptions/{exc_id}/assign",
        json={"assigned_to": str(test_operator_user.id)},
        headers=auth_headers,
    )
    # Then unassign by passing null
    resp = client.post(
        f"/api/exceptions/{exc_id}/assign",
        json={"assigned_to": None},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["assigned_to"] is None
    assert resp.json()["assignee_name"] is None


def test_assign_exception_invalid_user(client, auth_headers, active_exception):
    exc_id = active_exception["id"]
    fake_user_id = uuid.uuid4()
    resp = client.post(
        f"/api/exceptions/{exc_id}/assign",
        json={"assigned_to": str(fake_user_id)},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_assign_resolved_exception_fails(client, auth_headers, active_exception, test_operator_user):
    exc_id = active_exception["id"]
    # Move to investigating then resolve
    client.post(
        f"/api/exceptions/{exc_id}/status",
        json={"status": "investigating"},
        headers=auth_headers,
    )
    client.post(
        f"/api/exceptions/{exc_id}/resolve",
        json={"resolution_note": "Resolved ticket"},
        headers=auth_headers,
    )

    # Now attempt to reassign
    resp = client.post(
        f"/api/exceptions/{exc_id}/assign",
        json={"assigned_to": str(test_operator_user.id)},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "reopening" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 3. Status Transition Tests
# ---------------------------------------------------------------------------


def test_update_status_open_to_investigating(client, auth_headers, active_exception, db_session):
    exc_id = active_exception["id"]
    resp = client.post(
        f"/api/exceptions/{exc_id}/status",
        json={"status": "investigating", "note": "Beginning forensic check"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "investigating"

    # Verify audit log
    log = db_session.query(AuditLog).filter(
        AuditLog.entity_id == exc_id,
        AuditLog.action == "exception_status_changed",
    ).first()
    assert log is not None
    assert log.details["new_status"] == "investigating"


def test_update_status_invalid_direct_transition_to_resolved(client, auth_headers, active_exception):
    exc_id = active_exception["id"]
    resp = client.post(
        f"/api/exceptions/{exc_id}/status",
        json={"status": "resolved"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "resolve" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. Human Review Notes Tests
# ---------------------------------------------------------------------------


def test_add_review_note_success(client, auth_headers, active_exception, db_session):
    exc_id = active_exception["id"]
    resp = client.post(
        f"/api/exceptions/{exc_id}/review",
        json={"note": "Verified with payment gateway logs. Fee deduction was applied."},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "investigating"  # Auto-transitions to investigating
    assert "Fee deduction was applied" in data["reviewer_note"]

    # Verify audit log
    log = db_session.query(AuditLog).filter(
        AuditLog.entity_id == exc_id,
        AuditLog.action == "exception_reviewed",
    ).first()
    assert log is not None
    assert "Fee deduction was applied" in log.details["note"]


def test_add_review_note_empty_rejected(client, auth_headers, active_exception):
    exc_id = active_exception["id"]
    resp = client.post(
        f"/api/exceptions/{exc_id}/review",
        json={"note": "   "},
        headers=auth_headers,
    )
    assert resp.status_code in (400, 422)


def test_add_review_note_to_resolved_fails(client, auth_headers, active_exception):
    exc_id = active_exception["id"]
    client.post(
        f"/api/exceptions/{exc_id}/status",
        json={"status": "investigating"},
        headers=auth_headers,
    )
    client.post(
        f"/api/exceptions/{exc_id}/resolve",
        json={"resolution_note": "Discrepancy credited"},
        headers=auth_headers,
    )
    resp = client.post(
        f"/api/exceptions/{exc_id}/review",
        json={"note": "Late thought"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 5. Resolution & Ignore Tests
# ---------------------------------------------------------------------------


def test_resolve_exception_success(client, auth_headers, active_exception, db_session):
    exc_id = active_exception["id"]
    resp = client.post(
        f"/api/exceptions/{exc_id}/resolve",
        json={"resolution_note": "Manual ledger entry adjusted for gateway commission."},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "resolved"
    assert data["resolution_note"] == "Manual ledger entry adjusted for gateway commission."
    assert data["resolved_at"] is not None
    assert data["resolved_by"] is not None

    log = db_session.query(AuditLog).filter(
        AuditLog.entity_id == exc_id,
        AuditLog.action == "exception_resolved",
    ).first()
    assert log is not None
    assert "gateway commission" in log.details["resolution_note"]


def test_resolve_exception_empty_note_fails(client, auth_headers, active_exception):
    exc_id = active_exception["id"]
    resp = client.post(
        f"/api/exceptions/{exc_id}/resolve",
        json={"resolution_note": "   "},
        headers=auth_headers,
    )
    assert resp.status_code in (400, 422)


def test_resolve_already_resolved_fails(client, auth_headers, active_exception):
    exc_id = active_exception["id"]
    client.post(
        f"/api/exceptions/{exc_id}/resolve",
        json={"resolution_note": "First resolution note"},
        headers=auth_headers,
    )
    resp2 = client.post(
        f"/api/exceptions/{exc_id}/resolve",
        json={"resolution_note": "Second duplicate resolution"},
        headers=auth_headers,
    )
    assert resp2.status_code == 400
    assert "already been resolved" in resp2.json()["detail"]


def test_ignore_exception_success(client, auth_headers, active_exception, db_session):
    exc_id = active_exception["id"]
    resp = client.post(
        f"/api/exceptions/{exc_id}/ignore",
        json={"reason": "Sandbox test transaction outside production ledger."},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ignored"
    assert "[IGNORED]" in data["resolution_note"]
    assert data["ignored_at"] is not None
    assert data["ignored_by"] is not None

    log = db_session.query(AuditLog).filter(
        AuditLog.entity_id == exc_id,
        AuditLog.action == "exception_ignored",
    ).first()
    assert log is not None
    assert "Sandbox test transaction" in log.details["reason"]


def test_ignore_exception_empty_reason_fails(client, auth_headers, active_exception):
    exc_id = active_exception["id"]
    resp = client.post(
        f"/api/exceptions/{exc_id}/ignore",
        json={"reason": ""},
        headers=auth_headers,
    )
    assert resp.status_code in (400, 422)


def test_ignore_already_resolved_fails(client, auth_headers, active_exception):
    exc_id = active_exception["id"]
    client.post(
        f"/api/exceptions/{exc_id}/resolve",
        json={"resolution_note": "Properly resolved"},
        headers=auth_headers,
    )
    resp = client.post(
        f"/api/exceptions/{exc_id}/ignore",
        json={"reason": "Attempting to ignore resolved"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "already resolved" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 6. Escalation Tests
# ---------------------------------------------------------------------------


def test_escalate_exception_success(client, auth_headers, active_exception, db_session):
    exc_id = active_exception["id"]
    resp = client.post(
        f"/api/exceptions/{exc_id}/escalate",
        json={
            "reason": "Potential fraudulent activity detected across transaction batch",
            "suggested_team": "Risk & Fraud Engineering",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["escalated_at"] is not None
    assert "fraudulent activity" in data["escalation_reason"]
    assert data["status"] == "investigating"

    log = db_session.query(AuditLog).filter(
        AuditLog.entity_id == exc_id,
        AuditLog.action == "exception_escalated",
    ).first()
    assert log is not None
    assert log.details["suggested_team"] == "Risk & Fraud Engineering"


def test_escalate_resolved_exception_fails(client, auth_headers, active_exception):
    exc_id = active_exception["id"]
    client.post(
        f"/api/exceptions/{exc_id}/resolve",
        json={"resolution_note": "Case closed"},
        headers=auth_headers,
    )
    resp = client.post(
        f"/api/exceptions/{exc_id}/escalate",
        json={"reason": "Cannot escalate closed case"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# 7. Reopen Tests
# ---------------------------------------------------------------------------


def test_reopen_resolved_exception_success(client, auth_headers, active_exception, db_session):
    exc_id = active_exception["id"]
    # Resolve
    client.post(
        f"/api/exceptions/{exc_id}/resolve",
        json={"resolution_note": "Pre-mature close"},
        headers=auth_headers,
    )
    # Reopen
    resp = client.post(
        f"/api/exceptions/{exc_id}/reopen",
        json={"reason": "Customer called back with additional bank proof"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "investigating"
    assert data["resolved_at"] is None
    assert data["resolved_by"] is None
    assert "Customer called back with additional bank proof" in data["reviewer_note"]

    # Verify audit log
    log = db_session.query(AuditLog).filter(
        AuditLog.entity_id == exc_id,
        AuditLog.action == "exception_reopened",
    ).first()
    assert log is not None


def test_reopen_ignored_exception_success(client, auth_headers, active_exception):
    exc_id = active_exception["id"]
    client.post(
        f"/api/exceptions/{exc_id}/ignore",
        json={"reason": "Was believed to be testing"},
        headers=auth_headers,
    )
    resp = client.post(
        f"/api/exceptions/{exc_id}/reopen",
        json={"reason": "Turned out to be actual live merchant traffic"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "investigating"
    assert resp.json()["ignored_at"] is None
    assert resp.json()["ignored_by"] is None


def test_reopen_open_exception_fails(client, auth_headers, active_exception):
    exc_id = active_exception["id"]
    resp = client.post(
        f"/api/exceptions/{exc_id}/reopen",
        json={"reason": "Should fail because it is open"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "Only resolved or ignored" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# 8. Timeline & Details Tests
# ---------------------------------------------------------------------------


def test_get_exception_timeline(client, auth_headers, active_exception, test_operator_user):
    exc_id = active_exception["id"]
    # Generate some actions
    client.post(
        f"/api/exceptions/{exc_id}/assign",
        json={"assigned_to": str(test_operator_user.id)},
        headers=auth_headers,
    )
    client.post(
        f"/api/exceptions/{exc_id}/review",
        json={"note": "Timeline test review note"},
        headers=auth_headers,
    )

    resp = client.get(f"/api/exceptions/{exc_id}/timeline", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    events = data["events"]
    assert len(events) >= 2
    # Ensure all have valid structure
    for event in events:
        assert "event_type" in event
        assert "title" in event
        assert "timestamp" in event


def test_get_exception_details_with_evidence(client, auth_headers, sample_merchant, db_session):
    now = datetime.now(timezone.utc)
    txn = Transaction(
        id=uuid.uuid4(),
        merchant_id=sample_merchant.id,
        transaction_reference=f"TXN_{uuid.uuid4().hex[:8]}",
        amount=Decimal("1500.00"),
        currency="INR",
        status=TransactionStatus.success,
        payment_method="upi",
        transaction_date=now,
    )
    bank_txn = BankTransaction(
        id=uuid.uuid4(),
        bank_reference=f"BNK_{uuid.uuid4().hex[:8]}",
        amount=Decimal("1450.00"),
        status="posted",
        transaction_date=now,
    )
    db_session.add_all([txn, bank_txn])
    db_session.commit()

    recon = ReconciliationResult(
        id=uuid.uuid4(),
        transaction_id=txn.id,
        bank_transaction_id=bank_txn.id,
        match_status=MatchStatus.amount_mismatch,
        confidence_score=Decimal("0.8500"),
        difference_amount=Decimal("50.00"),
    )
    db_session.add(recon)
    db_session.commit()

    analysis = AIAnalysis(
        id=uuid.uuid4(),
        reconciliation_id=recon.id,
        analysis_type=AnalysisType.exception_analysis,
        summary="MDR fee deduction identified",
        root_cause="MDR fee deduction without gross settlement",
        risk_level=RiskLevel.low,
        confidence_score=Decimal("0.9200"),
        recommended_action="Accept variance under MDR rate schedule",
        ai_provider="rule_based",
        model_name="deterministic_v1",
    )
    db_session.add(analysis)
    db_session.commit()

    exc = PaymentException(
        id=uuid.uuid4(),
        reconciliation_id=recon.id,
        merchant_id=sample_merchant.id,
        severity=ExceptionSeverity.high,
        category="fee_discrepancy",
        title="INR 50 fee difference",
        status=ExceptionStatus.open,
    )
    db_session.add(exc)
    db_session.commit()

    resp = client.get(f"/api/exceptions/{exc.id}/details", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["exception"]["id"] == str(exc.id)
    assert data["transaction"]["reference_id"] == txn.transaction_reference
    assert data["bank_transaction"]["bank_reference"] == bank_txn.bank_reference
    assert data["reconciliation"]["match_status"] == "amount_mismatch"
    assert data["ai_analysis"]["root_cause"] == "MDR fee deduction without gross settlement"


def test_list_exceptions_search_and_pagination(client, auth_headers, sample_merchant):
    unique_keyword = f"UniqueAuditKey_{uuid.uuid4().hex[:6]}"
    client.post(
        "/api/exceptions",
        json={
            "severity": "medium",
            "category": "timing_difference",
            "title": f"Timing discrepancy {unique_keyword}",
            "description": "Cross day settlement delay",
            "status": "open",
            "merchant_id": str(sample_merchant.id),
        },
        headers=auth_headers,
    )

    resp = client.get(f"/api/exceptions?search={unique_keyword}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert unique_keyword in data["items"][0]["title"]
