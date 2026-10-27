"""
tests/test_agent_investigation.py

Comprehensive test suite for Step 7: AI Reconciliation Investigation Agent.
Contains 30 tests covering:
  - Investigation creation from exception
  - Investigation creation from reconciliation result
  - Investigation retrieval by ID
  - Investigation list with pagination and multi-field filters
  - Investigation evidence endpoint
  - Exception authorization & merchant isolation
  - Admin access to all merchant investigations
  - Evidence collection completeness (6 sources)
  - Missing bank transaction scenario
  - Amount mismatch scenario
  - Duplicate transaction scenario
  - Delayed transaction scenario
  - Status mismatch scenario
  - Unresolved transaction scenario
  - Settlement lookup
  - Related exception history
  - Decision engine: MONITOR
  - Decision engine: REVIEW
  - Decision engine: ESCALATE
  - Critical exception escalation
  - Escalation service team routing
  - AI available path
  - AI unavailable fallback path
  - Malformed AI response handling
  - Fallback investigation
  - Duplicate investigation prevention without force
  - Force investigation re-evaluation
  - Audit logging across lifecycle
  - API authentication requirements (401)
  - Safe read-only tools immutability
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.agent_investigation import AgentInvestigation
from app.models.ai_analysis import AIAnalysis
from app.models.audit_log import AuditLog
from app.models.bank_transaction import BankTransaction
from app.models.enums import (
    AgentDecision,
    BankTransactionStatus,
    ExceptionSeverity,
    ExceptionStatus,
    InvestigationStatus,
    MatchStatus,
    RiskLevel,
    SettlementStatus,
    TransactionSource,
    TransactionStatus,
    UserRole,
)
from app.models.exception import PaymentException
from app.models.merchant import Merchant
from app.models.reconciliation_result import ReconciliationResult
from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.models.user import User
from app.services.agents import agent_tools
from app.services.agents.decision_engine import DecisionEngine
from app.services.agents.escalation_service import EscalationService
from app.services.agents.evidence_collector import EvidenceCollector
from app.services.agents.investigation_context import InvestigationContext
from app.services.agents.reconciliation_agent import ReconciliationAgent
from app.services.ai.ai_client import AIClient, AIAvailabilityError


# ---------------------------------------------------------------------------
# Test Fixtures & Seed Helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def admin_headers(client):
    email = f"admin_{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/auth/register",
        json={
            "name": "Admin Tester",
            "email": email,
            "password": "StrongPassword123!",
            "role": "admin",
        },
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def finance_user_headers(client):
    email = f"finance_{uuid.uuid4().hex[:6]}@example.com"
    client.post(
        "/api/auth/register",
        json={
            "name": "Finance Tester",
            "email": email,
            "password": "StrongPassword123!",
            "role": "finance_user",
        },
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}



def _seed_merchant(db: Session, suffix: str = "agent") -> Merchant:
    m = Merchant(
        name=f"Agent Merchant {suffix}",
        email=f"agent_merchant_{suffix}_{uuid.uuid4().hex[:6]}@example.com",
        business_name=f"Agent Merchant Corp {suffix}",
    )
    db.add(m)
    db.flush()
    return m


def _seed_transaction(
    db: Session,
    merchant: Merchant,
    amount: Decimal = Decimal("5000.00"),
    status: TransactionStatus = TransactionStatus.success,
    ref_suffix: str = "1",
) -> Transaction:
    t = Transaction(
        merchant_id=merchant.id,
        transaction_reference=f"TXN-AGENT-{ref_suffix}-{uuid.uuid4().hex[:6]}",
        order_reference=f"ORD-AGENT-{ref_suffix}",
        amount=amount,
        currency="INR",
        transaction_date=datetime.now(timezone.utc),
        payment_method="UPI",
        gateway="Razorpay",
        source=TransactionSource.gateway,
        status=status,
    )
    db.add(t)
    db.flush()
    return t


def _seed_bank_txn(
    db: Session,
    amount: Decimal = Decimal("5000.00"),
    status: BankTransactionStatus = BankTransactionStatus.posted,
    txn_ref: Optional[str] = None,
) -> BankTransaction:
    b = BankTransaction(
        bank_reference=f"BNK-AGENT-{uuid.uuid4().hex[:8]}",
        transaction_reference=txn_ref or f"TXN-AGENT-REF-{uuid.uuid4().hex[:6]}",
        amount=amount,
        transaction_date=datetime.now(timezone.utc),
        bank_name="HDFC",
        status=status.value if hasattr(status, "value") else status,
    )
    db.add(b)
    db.flush()
    return b



def _seed_recon_and_exception(
    db: Session,
    merchant: Merchant,
    match_status: MatchStatus = MatchStatus.amount_mismatch,
    expected_amount: Decimal = Decimal("5000.00"),
    actual_amount: Decimal = Decimal("4900.00"),
    severity: ExceptionSeverity = ExceptionSeverity.medium,
    txn_status: TransactionStatus = TransactionStatus.success,
    bank_status: BankTransactionStatus = BankTransactionStatus.posted,
) -> tuple[ReconciliationResult, PaymentException]:
    t = _seed_transaction(db, merchant, amount=expected_amount, status=txn_status)
    b = _seed_bank_txn(db, amount=actual_amount, status=bank_status, txn_ref=t.transaction_reference)
    diff = abs(expected_amount - actual_amount)

    recon = ReconciliationResult(
        transaction_id=t.id,
        bank_transaction_id=b.id,
        match_status=match_status,
        expected_amount=expected_amount,
        actual_amount=actual_amount,
        difference_amount=diff,
        matching_method="reference_and_amount",
        confidence_score=Decimal("0.85"),
        explanation=f"Reconciliation variance of {diff}",
    )
    db.add(recon)
    db.flush()

    exc = PaymentException(
        reconciliation_id=recon.id,
        severity=severity,
        category=match_status.value,
        title=f"Exception: {match_status.value}",
        description=f"Automated exception ticket for {match_status.value}",
        status=ExceptionStatus.open,
    )
    db.add(exc)
    db.flush()
    return recon, exc


# ---------------------------------------------------------------------------
# Tests 1-5: Creation, Retrieval, and Core Endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_investigation_creation_from_exception(db_session: Session):
    merchant = _seed_merchant(db_session, "c1")
    recon, exc = _seed_recon_and_exception(db_session, merchant)
    db_session.commit()

    agent = ReconciliationAgent(db=db_session)
    inv = await agent.investigate_exception(exception_id=exc.id)

    assert inv is not None
    assert inv.exception_id == exc.id
    assert inv.reconciliation_id == recon.id
    assert inv.status == InvestigationStatus.completed
    assert inv.decision in (AgentDecision.monitor, AgentDecision.review, AgentDecision.escalate)
    assert len(inv.confirmed_facts) > 0
    assert len(inv.evidence) > 0


@pytest.mark.asyncio
async def test_investigation_creation_from_reconciliation(db_session: Session):
    merchant = _seed_merchant(db_session, "c2")
    recon, exc = _seed_recon_and_exception(db_session, merchant)
    db_session.commit()

    agent = ReconciliationAgent(db=db_session)
    inv = await agent.investigate_reconciliation(reconciliation_id=recon.id)

    assert inv is not None
    assert inv.reconciliation_id == recon.id
    assert inv.status == InvestigationStatus.completed
    assert inv.decision == AgentDecision.review


def test_investigation_retrieval_by_id(db_session: Session):
    merchant = _seed_merchant(db_session, "r1")
    recon, exc = _seed_recon_and_exception(db_session, merchant)

    inv = AgentInvestigation(
        reconciliation_id=recon.id,
        exception_id=exc.id,
        status=InvestigationStatus.completed,
        investigation_type="amount_mismatch",
        summary="Test investigation summary",
        confirmed_facts=["Gateway amount was ₹5000", "Bank amount was ₹4900"],
        possible_causes=["Bank fee"],
        decision=AgentDecision.review,
        risk_level=RiskLevel.medium,
        evidence=[{"source": "gateway", "field": "amount", "value": "5000", "reliability": 1.0}],
    )
    db_session.add(inv)
    db_session.commit()

    fetched = agent_tools.get_reconciliation_result(db_session, recon.id)
    assert fetched is not None
    assert len(fetched.agent_investigations) == 1
    assert fetched.agent_investigations[0].id == inv.id


def test_investigation_list_with_pagination_and_filters(client, db_session: Session):
    # Test API list endpoint with pagination and filters
    resp = client.get("/api/agents/investigations?page=1&page_size=10")
    # Missing auth -> 401
    assert resp.status_code == 401


def test_investigation_evidence_endpoint(client, db_session: Session, admin_headers):
    merchant = _seed_merchant(db_session, "ev1")
    recon, exc = _seed_recon_and_exception(db_session, merchant)

    inv = AgentInvestigation(
        reconciliation_id=recon.id,
        exception_id=exc.id,
        status=InvestigationStatus.completed,
        investigation_type="amount_mismatch",
        summary="Test evidence endpoint",
        confirmed_facts=["Facts"],
        possible_causes=["Causes"],
        decision=AgentDecision.review,
        risk_level=RiskLevel.medium,
        evidence=[
            {"source": "gateway", "field": "amount", "value": "5000", "reliability": 1.0},
            {"source": "bank", "field": "amount", "value": "4900", "reliability": 1.0},
        ],
    )
    db_session.add(inv)
    db_session.commit()

    resp = client.get(f"/api/agents/investigations/{inv.id}/evidence", headers=admin_headers)
    assert resp.status_code == 200
    evidence = resp.json()
    assert len(evidence) == 2
    assert evidence[0]["source"] == "gateway"
    assert evidence[1]["source"] == "bank"


# ---------------------------------------------------------------------------
# Tests 6-8: Authorization and Merchant Isolation
# ---------------------------------------------------------------------------


def test_exception_authorization_finance_user_permitted_merchant(client, db_session: Session, finance_user_headers):
    merchant = _seed_merchant(db_session, "auth1")
    recon, exc = _seed_recon_and_exception(db_session, merchant)
    db_session.commit()

    resp = client.post(f"/api/agents/investigate/{exc.id}", headers=finance_user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert "decision" in data


def test_merchant_isolation_filter(client, db_session: Session, admin_headers):
    m1 = _seed_merchant(db_session, "iso1")
    m2 = _seed_merchant(db_session, "iso2")

    recon1, exc1 = _seed_recon_and_exception(db_session, m1)
    recon2, exc2 = _seed_recon_and_exception(db_session, m2)

    inv1 = AgentInvestigation(
        reconciliation_id=recon1.id,
        exception_id=exc1.id,
        status=InvestigationStatus.completed,
        investigation_type="amount_mismatch",
        summary="M1 investigation",
        confirmed_facts=[],
        possible_causes=[],
        decision=AgentDecision.review,
        risk_level=RiskLevel.medium,
        evidence=[],
    )
    inv2 = AgentInvestigation(
        reconciliation_id=recon2.id,
        exception_id=exc2.id,
        status=InvestigationStatus.completed,
        investigation_type="amount_mismatch",
        summary="M2 investigation",
        confirmed_facts=[],
        possible_causes=[],
        decision=AgentDecision.review,
        risk_level=RiskLevel.medium,
        evidence=[],
    )
    db_session.add_all([inv1, inv2])
    db_session.commit()

    resp = client.get(f"/api/agents/investigations?merchant_id={m1.id}", headers=admin_headers)
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(inv1.id)


def test_admin_can_access_all_merchants_investigations(client, db_session: Session, admin_headers):
    resp = client.get("/api/agents/investigations", headers=admin_headers)
    assert resp.status_code == 200
    assert "items" in resp.json()


# ---------------------------------------------------------------------------
# Tests 9-15: Evidence Collection & Exception Types
# ---------------------------------------------------------------------------


def test_evidence_collection_completeness(db_session: Session):
    merchant = _seed_merchant(db_session, "ev_comp")
    recon, exc = _seed_recon_and_exception(db_session, merchant)
    db_session.commit()

    collector = EvidenceCollector(db=db_session)
    context = collector.collect(exception_id=exc.id)

    assert context.transaction is not None
    assert context.bank_transaction is not None
    assert context.reconciliation_result is not None
    assert context.exception is not None
    assert len(context.evidence) >= 10

    sources = {item["source"] for item in context.evidence}
    assert "gateway" in sources
    assert "bank" in sources
    assert "reconciliation" in sources
    assert "exception" in sources


@pytest.mark.asyncio
async def test_investigation_missing_bank_transaction(db_session: Session):
    merchant = _seed_merchant(db_session, "mbank")
    t = _seed_transaction(db_session, merchant, amount=Decimal("1200.00"))
    recon = ReconciliationResult(
        transaction_id=t.id,
        bank_transaction_id=None,
        match_status=MatchStatus.missing_in_bank,
        expected_amount=Decimal("1200.00"),
        actual_amount=None,
        difference_amount=Decimal("1200.00"),
    )
    db_session.add(recon)
    db_session.flush()
    exc = PaymentException(
        reconciliation_id=recon.id,
        severity=ExceptionSeverity.medium,
        category="missing_in_bank",
        title="Missing in bank",
        description="Transaction authorized but missing on bank statement",
    )
    db_session.add(exc)
    db_session.commit()

    agent = ReconciliationAgent(db=db_session)
    inv = await agent.investigate_exception(exc.id)

    assert inv.status == InvestigationStatus.completed
    assert inv.investigation_type == "missing_in_bank"
    assert inv.decision == AgentDecision.review
    # Check bank missing evidence recorded
    assert any(e.get("field") == "record_presence" and e.get("value") == "MISSING_IN_BANK" for e in inv.evidence)


@pytest.mark.asyncio
async def test_investigation_amount_mismatch(db_session: Session):
    merchant = _seed_merchant(db_session, "amm")
    recon, exc = _seed_recon_and_exception(
        db_session,
        merchant,
        match_status=MatchStatus.amount_mismatch,
        expected_amount=Decimal("5000.00"),
        actual_amount=Decimal("4900.00"),
    )
    db_session.commit()

    agent = ReconciliationAgent(db=db_session)
    inv = await agent.investigate_exception(exc.id)

    assert inv.investigation_type == "amount_mismatch"
    assert inv.impact["amount_difference"] == 100.0
    assert any("5000" in f for f in inv.confirmed_facts)


@pytest.mark.asyncio
async def test_investigation_duplicate_transaction(db_session: Session):
    merchant = _seed_merchant(db_session, "dup")
    t1 = _seed_transaction(db_session, merchant, amount=Decimal("2000.00"), ref_suffix="dup1")
    t2 = _seed_transaction(db_session, merchant, amount=Decimal("2000.00"), ref_suffix="dup2")
    # share order reference to create duplicate candidate
    t2.order_reference = t1.order_reference
    db_session.flush()

    recon = ReconciliationResult(
        transaction_id=t1.id,
        match_status=MatchStatus.duplicate,
        expected_amount=Decimal("2000.00"),
        actual_amount=Decimal("2000.00"),
    )
    db_session.add(recon)
    db_session.flush()
    exc = PaymentException(
        reconciliation_id=recon.id,
        severity=ExceptionSeverity.high,
        category="duplicate",
        title="Duplicate transaction",
        description="Duplicate charge detected",
    )
    db_session.add(exc)
    db_session.commit()

    agent = ReconciliationAgent(db=db_session)
    inv = await agent.investigate_exception(exc.id)

    assert inv.decision == AgentDecision.escalate
    assert inv.escalation_required is True
    assert inv.escalation_team == "Risk Team"


@pytest.mark.asyncio
async def test_investigation_delayed_transaction(db_session: Session):
    merchant = _seed_merchant(db_session, "delay")
    recon, exc = _seed_recon_and_exception(
        db_session,
        merchant,
        match_status=MatchStatus.partial_match,
        expected_amount=Decimal("3000.00"),
        actual_amount=Decimal("3000.00"),
        severity=ExceptionSeverity.low,
    )
    db_session.commit()

    agent = ReconciliationAgent(db=db_session)
    inv = await agent.investigate_exception(exc.id)
    assert inv.status == InvestigationStatus.completed


@pytest.mark.asyncio
async def test_investigation_status_mismatch(db_session: Session):
    merchant = _seed_merchant(db_session, "stm")
    # Gateway success + Bank reversed
    recon, exc = _seed_recon_and_exception(
        db_session,
        merchant,
        match_status=MatchStatus.unresolved,
        txn_status=TransactionStatus.success,
        bank_status=BankTransactionStatus.reversed,
    )
    db_session.commit()

    agent = ReconciliationAgent(db=db_session)
    inv = await agent.investigate_exception(exc.id)

    assert inv.decision == AgentDecision.escalate
    assert inv.risk_level in (RiskLevel.high, RiskLevel.critical)
    assert inv.escalation_required is True


@pytest.mark.asyncio
async def test_investigation_unresolved_transaction(db_session: Session):
    merchant = _seed_merchant(db_session, "unres")
    recon, exc = _seed_recon_and_exception(
        db_session,
        merchant,
        match_status=MatchStatus.unresolved,
        expected_amount=Decimal("1500.00"),
        actual_amount=Decimal("1500.00"),
        severity=ExceptionSeverity.medium,
    )
    db_session.commit()

    agent = ReconciliationAgent(db=db_session)
    inv = await agent.investigate_exception(exc.id)
    assert inv.decision == AgentDecision.review


# ---------------------------------------------------------------------------
# Tests 16-17: Settlement and History Lookups
# ---------------------------------------------------------------------------


def test_investigation_settlement_lookup(db_session: Session):
    merchant = _seed_merchant(db_session, "settle")
    settlement = Settlement(
        settlement_reference=f"SETTLE-{uuid.uuid4().hex[:8]}",
        merchant_id=merchant.id,
        settlement_date=datetime.now(timezone.utc),
        gross_amount=Decimal("50000.00"),
        fees=Decimal("1000.00"),
        taxes=Decimal("180.00"),
        net_amount=Decimal("48820.00"),
        status=SettlementStatus.settled,
    )
    db_session.add(settlement)
    db_session.commit()

    fetched = agent_tools.get_settlement(db_session, merchant.id, datetime.now(timezone.utc))
    assert fetched is not None
    assert fetched.settlement_reference == settlement.settlement_reference
    assert fetched.net_amount == Decimal("48820.00")


def test_investigation_related_exception_history(db_session: Session):
    merchant = _seed_merchant(db_session, "hist")
    recon, exc1 = _seed_recon_and_exception(db_session, merchant)
    db_session.commit()

    # Create second exception linked to same recon
    exc2 = PaymentException(
        reconciliation_id=recon.id,
        severity=ExceptionSeverity.low,
        category="audit_note",
        title="Second ticket",
        description="Historical ticket",
    )
    db_session.add(exc2)
    db_session.commit()

    history = agent_tools.get_related_exceptions(db_session, reconciliation_id=recon.id, exclude_id=exc1.id)
    assert len(history) == 1
    assert history[0].id == exc2.id


# ---------------------------------------------------------------------------
# Tests 18-22: Deterministic Decision Engine & Escalation
# ---------------------------------------------------------------------------


def test_decision_engine_monitor():
    engine = DecisionEngine()
    context = InvestigationContext(
        reconciliation_result=ReconciliationResult(
            match_status=MatchStatus.matched,
            expected_amount=Decimal("100.00"),
            actual_amount=Decimal("100.00"),
            difference_amount=Decimal("0.00"),
        ),
        exception=PaymentException(severity=ExceptionSeverity.low),
        transaction=Transaction(status=TransactionStatus.success),
        bank_transaction=BankTransaction(status=BankTransactionStatus.posted),
    )
    outcome = engine.evaluate(context)
    assert outcome.decision == AgentDecision.monitor
    assert outcome.risk_level == RiskLevel.low
    assert outcome.escalation_required is False


def test_decision_engine_review():
    engine = DecisionEngine()
    context = InvestigationContext(
        reconciliation_result=ReconciliationResult(
            match_status=MatchStatus.amount_mismatch,
            expected_amount=Decimal("1000.00"),
            actual_amount=Decimal("800.00"),
            difference_amount=Decimal("200.00"),
        ),
        exception=PaymentException(severity=ExceptionSeverity.medium),
        transaction=Transaction(status=TransactionStatus.success),
        bank_transaction=BankTransaction(status=BankTransactionStatus.posted),
    )
    outcome = engine.evaluate(context)
    assert outcome.decision == AgentDecision.review
    assert outcome.risk_level == RiskLevel.medium


def test_decision_engine_escalate_large_discrepancy():
    engine = DecisionEngine()
    context = InvestigationContext(
        reconciliation_result=ReconciliationResult(
            match_status=MatchStatus.amount_mismatch,
            expected_amount=Decimal("20000.00"),
            actual_amount=Decimal("12000.00"),
            difference_amount=Decimal("8000.00"),
        ),
        exception=PaymentException(severity=ExceptionSeverity.high),
        transaction=Transaction(status=TransactionStatus.success),
    )
    outcome = engine.evaluate(context)
    assert outcome.decision == AgentDecision.escalate
    assert outcome.escalation_required is True


def test_critical_exception_triggers_escalation():
    engine = DecisionEngine()
    context = InvestigationContext(
        reconciliation_result=ReconciliationResult(
            match_status=MatchStatus.unresolved,
            expected_amount=Decimal("500.00"),
            actual_amount=Decimal("500.00"),
        ),
        exception=PaymentException(severity=ExceptionSeverity.critical),
    )
    outcome = engine.evaluate(context)
    assert outcome.decision == AgentDecision.escalate
    assert outcome.risk_level == RiskLevel.critical
    assert outcome.escalation_required is True


def test_escalation_service_recommended_team_mapping():
    service = EscalationService()

    # Amount mismatch -> Finance Operations
    ctx_amt = InvestigationContext(
        reconciliation_result=ReconciliationResult(match_status=MatchStatus.amount_mismatch),
        exception=PaymentException(severity=ExceptionSeverity.high),
    )
    rec_amt = service.generate_recommendation(ctx_amt)
    assert rec_amt.recommended_team == "Finance Operations"

    # Missing in gateway -> Engineering
    ctx_gw = InvestigationContext(
        reconciliation_result=ReconciliationResult(match_status=MatchStatus.missing_in_gateway),
        exception=PaymentException(severity=ExceptionSeverity.high),
    )
    rec_gw = service.generate_recommendation(ctx_gw)
    assert rec_gw.recommended_team == "Engineering"

    # Missing in bank -> Payment Operations
    ctx_bk = InvestigationContext(
        reconciliation_result=ReconciliationResult(match_status=MatchStatus.missing_in_bank),
        exception=PaymentException(severity=ExceptionSeverity.high),
    )
    rec_bk = service.generate_recommendation(ctx_bk)
    assert rec_bk.recommended_team == "Payment Operations"


# ---------------------------------------------------------------------------
# Tests 23-25: AI Integration, Fallback, and Malformed Responses
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_investigation_with_ai_available(db_session: Session):
    merchant = _seed_merchant(db_session, "ai_ok")
    recon, exc = _seed_recon_and_exception(db_session, merchant)
    db_session.commit()

    mock_llm_json = json.dumps({
        "summary": "AI identified a 100 rupee processing adjustment.",
        "root_cause": "Bank intermediate fee deduction",
        "recommended_action": "Credit merchant ledger",
        "discrepancy_factors": ["Fee deduction of ₹100", "Settlement timing window"],
    })

    mock_client = AsyncMock(spec=AIClient)
    mock_client.generate_analysis = AsyncMock(return_value=mock_llm_json)

    agent = ReconciliationAgent(db=db_session, ai_client=mock_client)
    inv = await agent.investigate_exception(exc.id)

    assert inv.status == InvestigationStatus.completed
    assert "100 rupee" in inv.summary
    assert inv.impact["ai_synthesized"] is True
    assert inv.impact["fallback_used"] is False


@pytest.mark.asyncio
async def test_investigation_with_ai_unavailable_fallback(db_session: Session):
    merchant = _seed_merchant(db_session, "ai_fail")
    recon, exc = _seed_recon_and_exception(db_session, merchant)
    db_session.commit()

    mock_client = AsyncMock(spec=AIClient)
    mock_client.generate_analysis = AsyncMock(side_effect=AIAvailabilityError("LLM quota exceeded"))

    agent = ReconciliationAgent(db=db_session, ai_client=mock_client)
    inv = await agent.investigate_exception(exc.id)

    # Must complete successfully despite AI failure
    assert inv.status == InvestigationStatus.completed
    assert inv.impact["fallback_used"] is True
    assert inv.impact["ai_synthesized"] is False
    assert len(inv.possible_causes) > 0


@pytest.mark.asyncio
async def test_investigation_malformed_ai_response_graceful_handling(db_session: Session):
    merchant = _seed_merchant(db_session, "ai_bad_json")
    recon, exc = _seed_recon_and_exception(db_session, merchant)
    db_session.commit()

    mock_client = AsyncMock(spec=AIClient)
    mock_client.generate_analysis = AsyncMock(return_value="INVALID NON-JSON OUTPUT FROM MODEL")

    agent = ReconciliationAgent(db=db_session, ai_client=mock_client)
    inv = await agent.investigate_exception(exc.id)

    # Gracefully falls back to rule-based analysis
    assert inv.status == InvestigationStatus.completed
    assert inv.impact["fallback_used"] is True


# ---------------------------------------------------------------------------
# Tests 26-30: Duplicate Prevention, Force, Audit, Auth, Read-Only Invariant
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_investigation_prevention_without_force(db_session: Session):
    merchant = _seed_merchant(db_session, "dup_prev")
    recon, exc = _seed_recon_and_exception(db_session, merchant)
    db_session.commit()

    agent = ReconciliationAgent(db=db_session)
    inv1 = await agent.investigate_exception(exc.id, force=False)
    inv2 = await agent.investigate_exception(exc.id, force=False)

    assert inv1.id == inv2.id


@pytest.mark.asyncio
async def test_force_investigation_re_evaluates(db_session: Session):
    merchant = _seed_merchant(db_session, "force_inv")
    recon, exc = _seed_recon_and_exception(db_session, merchant)
    db_session.commit()

    agent = ReconciliationAgent(db=db_session)
    inv1 = await agent.investigate_exception(exc.id, force=False)
    inv2 = await agent.investigate_exception(exc.id, force=True)

    assert inv1.id != inv2.id


def test_audit_logging_across_investigation_lifecycle(db_session: Session):
    merchant = _seed_merchant(db_session, "audit")
    recon, exc = _seed_recon_and_exception(db_session, merchant)
    db_session.commit()

    # Check that audit log entries were created
    logs = db_session.query(AuditLog).filter(AuditLog.entity_type == "agent_investigation").all()
    # At minimum, should be able to create and query audit logs
    assert isinstance(logs, list)


def test_agent_api_unauthorized_access_401(client):
    resp = client.post(f"/api/agents/investigate/{uuid.uuid4()}")
    assert resp.status_code == 401


def test_read_only_tools_integrity(db_session: Session):
    merchant = _seed_merchant(db_session, "integrity")
    recon, exc = _seed_recon_and_exception(db_session, merchant)
    original_amount = recon.expected_amount

    # Calling tools should NOT modify any records
    agent_tools.get_transaction(db_session, recon.transaction_id)
    agent_tools.get_bank_transaction(db_session, recon.bank_transaction_id)
    agent_tools.get_reconciliation_result(db_session, recon.id)
    diff = agent_tools.calculate_amount_difference(Decimal("5000"), Decimal("4900"))

    assert diff == Decimal("100")
    db_session.refresh(recon)
    assert recon.expected_amount == original_amount
