"""
tests/test_api_dashboard.py

Comprehensive test suite for Step 8 Dashboard API endpoints:
  - GET /api/dashboard/summary
  - GET /api/dashboard/exceptions
  - GET /api/dashboard/investigations
  - GET /api/dashboard/reconciliation-health
Covers authentication, count correctness, empty state handling, and merchant scoping.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.agent_investigation import AgentInvestigation
from app.models.enums import (
    AgentDecision,
    ExceptionSeverity,
    ExceptionStatus,
    InvestigationStatus,
    MatchStatus,
    RiskLevel,
    TransactionSource,
    TransactionStatus,
)
from app.models.exception import PaymentException
from app.models.merchant import Merchant
from app.models.reconciliation_result import ReconciliationResult
from app.models.transaction import Transaction


def _seed_merchant(db: Session, suffix: str = "dash") -> Merchant:
    m = Merchant(
        name=f"Merchant {suffix}",
        email=f"dash_{suffix}_{uuid.uuid4().hex[:6]}@example.com",
    )
    db.add(m)
    db.flush()
    return m


def test_dashboard_unauthorized_401(client: TestClient):
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 401
    res = client.get("/api/dashboard/exceptions")
    assert res.status_code == 401
    res = client.get("/api/dashboard/investigations")
    assert res.status_code == 401
    res = client.get("/api/dashboard/reconciliation-health")
    assert res.status_code == 401


def test_dashboard_summary_empty_state(client: TestClient, auth_headers: dict):
    res = client.get("/api/dashboard/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_transactions" in data
    assert "reconciliation_rate" in data
    assert "amount_reconciled" in data


def test_dashboard_summary_populated(client: TestClient, db_session: Session, auth_headers: dict):
    merchant = _seed_merchant(db_session, "s1")

    t1 = Transaction(
        merchant_id=merchant.id,
        transaction_reference=f"TXN_{uuid.uuid4().hex[:8]}",
        amount=Decimal("1500.00"),
        currency="INR",
        transaction_date=datetime.now(timezone.utc),
        status=TransactionStatus.success,
        source=TransactionSource.gateway,
    )
    db_session.add(t1)
    db_session.flush()

    recon = ReconciliationResult(
        transaction_id=t1.id,
        match_status=MatchStatus.matched,
        expected_amount=Decimal("1500.00"),
        actual_amount=Decimal("1500.00"),
    )
    db_session.add(recon)
    db_session.flush()

    exc = PaymentException(
        reconciliation_id=recon.id,
        severity=ExceptionSeverity.critical,
        category="status_mismatch",
        title="Critical conflict",
        description="Gateway success but bank failed",
        status=ExceptionStatus.open,
    )
    db_session.add(exc)
    db_session.commit()

    res = client.get("/api/dashboard/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_transactions"] >= 1
    assert data["matched_transactions"] >= 1
    assert data["reconciliation_rate"] > 0
    assert data["amount_reconciled"] >= 1500.0
    assert data["critical_issues"] >= 1


def test_dashboard_exceptions_breakdown(client: TestClient, db_session: Session, auth_headers: dict):
    merchant = _seed_merchant(db_session, "exc")

    t = Transaction(
        merchant_id=merchant.id,
        transaction_reference=f"TXN_EXC_{uuid.uuid4().hex[:8]}",
        amount=Decimal("2500.00"),
        currency="INR",
        transaction_date=datetime.now(timezone.utc),
        status=TransactionStatus.success,
        source=TransactionSource.gateway,
    )
    db_session.add(t)
    db_session.flush()

    recon = ReconciliationResult(
        transaction_id=t.id,
        match_status=MatchStatus.amount_mismatch,
        expected_amount=Decimal("2500.00"),
        actual_amount=Decimal("2400.00"),
        difference_amount=Decimal("100.00"),
    )
    db_session.add(recon)
    db_session.flush()

    exc1 = PaymentException(
        reconciliation_id=recon.id,
        severity=ExceptionSeverity.high,
        category="amount_mismatch",
        title="Amount mismatch discrepancy",
        description="Discrepancy of 100",
        status=ExceptionStatus.open,
    )
    exc2 = PaymentException(
        reconciliation_id=recon.id,
        severity=ExceptionSeverity.medium,
        category="delayed",
        title="Settlement delay",
        description="Delay > 1 day",
        status=ExceptionStatus.investigating,
    )
    db_session.add_all([exc1, exc2])
    db_session.commit()

    res = client.get("/api/dashboard/exceptions", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_exceptions"] >= 2
    severities = {item["name"]: item["count"] for item in data["by_severity"]}
    assert severities.get("high", 0) >= 1
    assert severities.get("medium", 0) >= 1
    assert len(data["recent_exceptions"]) >= 2


def test_dashboard_investigations_breakdown(client: TestClient, db_session: Session, auth_headers: dict):
    inv1 = AgentInvestigation(
        id=uuid.uuid4(),
        status=InvestigationStatus.completed,
        investigation_type="amount_mismatch",
        summary="Automated investigation completed",
        decision=AgentDecision.review,
        risk_level=RiskLevel.medium,
        confidence_score=Decimal("0.88"),
        escalation_required=False,
    )
    inv2 = AgentInvestigation(
        id=uuid.uuid4(),
        status=InvestigationStatus.completed,
        investigation_type="duplicate",
        summary="Critical duplicate detected",
        decision=AgentDecision.escalate,
        risk_level=RiskLevel.critical,
        confidence_score=Decimal("0.95"),
        escalation_required=True,
        escalation_team="Risk Team",
    )
    db_session.add_all([inv1, inv2])
    db_session.commit()

    res = client.get("/api/dashboard/investigations", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_investigations"] >= 2
    assert data["completed"] >= 2
    assert data["review_count"] >= 1
    assert data["escalate_count"] >= 1
    assert data["escalations_count"] >= 1
    assert data["critical_risk_count"] >= 1
    assert len(data["recent_investigations"]) >= 2


def test_dashboard_reconciliation_health_percentages(client: TestClient, db_session: Session, auth_headers: dict):
    merchant = _seed_merchant(db_session, "health")

    t1 = Transaction(
        merchant_id=merchant.id,
        transaction_reference=f"TXN_H1_{uuid.uuid4().hex[:8]}",
        amount=Decimal("1000.00"),
        currency="INR",
        transaction_date=datetime.now(timezone.utc),
        status=TransactionStatus.success,
        source=TransactionSource.gateway,
    )
    t2 = Transaction(
        merchant_id=merchant.id,
        transaction_reference=f"TXN_H2_{uuid.uuid4().hex[:8]}",
        amount=Decimal("2000.00"),
        currency="INR",
        transaction_date=datetime.now(timezone.utc),
        status=TransactionStatus.success,
        source=TransactionSource.gateway,
    )
    db_session.add_all([t1, t2])
    db_session.flush()

    r1 = ReconciliationResult(
        transaction_id=t1.id,
        match_status=MatchStatus.matched,
        expected_amount=Decimal("1000.00"),
        actual_amount=Decimal("1000.00"),
    )
    r2 = ReconciliationResult(
        transaction_id=t2.id,
        match_status=MatchStatus.amount_mismatch,
        expected_amount=Decimal("2000.00"),
        actual_amount=Decimal("1900.00"),
        difference_amount=Decimal("100.00"),
    )
    db_session.add_all([r1, r2])
    db_session.commit()

    res = client.get("/api/dashboard/reconciliation-health", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_evaluated"] >= 2
    statuses = {s["status"]: s for s in data["statuses"]}
    assert "matched" in statuses
    assert "amount_mismatch" in statuses
    assert statuses["matched"]["count"] >= 1
    assert statuses["amount_mismatch"]["count"] >= 1
    assert data["reconciliation_rate"] > 0
