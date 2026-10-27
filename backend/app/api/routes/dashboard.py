"""
app/api/routes/dashboard.py

FastAPI endpoints providing real aggregated metrics for the Finance Operations Control Center.
Includes KPI summaries, reconciliation health distributions, exception analytics,
and AI agent investigation overviews.
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db_session
from app.models.agent_investigation import AgentInvestigation
from app.models.enums import (
    AgentDecision,
    ExceptionSeverity,
    InvestigationStatus,
    MatchStatus,
    RiskLevel,
    UserRole,
)
from app.models.exception import PaymentException
from app.models.reconciliation_result import ReconciliationResult
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.dashboard import (
    DashboardExceptionsResponse,
    DashboardInvestigationsResponse,
    DashboardReconciliationHealthResponse,
    DashboardSummaryResponse,
    MetricCount,
    RecentExceptionItem,
    RecentInvestigationItem,
    ReconciliationHealthStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _apply_merchant_filter(query, model, merchant_id: Optional[uuid.UUID]):
    """Applies merchant scoping if merchant_id is provided."""
    if merchant_id:
        return query.filter(model.merchant_id == merchant_id)
    return query


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get top-level KPI metrics for finance operations dashboard",
)
def get_dashboard_summary(
    merchant_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> DashboardSummaryResponse:
    """Computes total transactions, matched volume, exceptions, and reconciliation rates."""
    # 1. Total transactions
    txn_query = db.query(func.count(Transaction.id))
    txn_query = _apply_merchant_filter(txn_query, Transaction, merchant_id)
    total_txns = txn_query.scalar() or 0

    # 2. Matched transactions & reconciled volume
    recon_query = db.query(
        func.count(ReconciliationResult.id),
        func.coalesce(func.sum(ReconciliationResult.actual_amount), Decimal("0")),
    ).filter(
        ReconciliationResult.match_status.in_([
            MatchStatus.matched,
            MatchStatus.partial_match,
        ])
    )
    if merchant_id:
        recon_query = recon_query.join(Transaction, ReconciliationResult.transaction_id == Transaction.id).filter(
            Transaction.merchant_id == merchant_id
        )

    matched_count, amount_sum = recon_query.first() or (0, Decimal("0"))
    matched_count = matched_count or 0
    amount_reconciled = float(amount_sum or 0)

    # 3. Exceptions count & critical issues
    exc_query = db.query(func.count(PaymentException.id))
    crit_query = db.query(func.count(PaymentException.id)).filter(
        PaymentException.severity == ExceptionSeverity.critical
    )
    if merchant_id:
        exc_query = exc_query.join(
            ReconciliationResult, PaymentException.reconciliation_id == ReconciliationResult.id
        ).join(
            Transaction, ReconciliationResult.transaction_id == Transaction.id
        ).filter(Transaction.merchant_id == merchant_id)
        crit_query = crit_query.join(
            ReconciliationResult, PaymentException.reconciliation_id == ReconciliationResult.id
        ).join(
            Transaction, ReconciliationResult.transaction_id == Transaction.id
        ).filter(Transaction.merchant_id == merchant_id)

    total_exceptions = exc_query.scalar() or 0
    critical_issues = crit_query.scalar() or 0

    # Rate calculation
    recon_rate = round((matched_count / total_txns * 100.0), 2) if total_txns > 0 else 0.0

    return DashboardSummaryResponse(
        total_transactions=total_txns,
        matched_transactions=matched_count,
        exceptions_count=total_exceptions,
        reconciliation_rate=recon_rate,
        amount_reconciled=amount_reconciled,
        critical_issues=critical_issues,
    )


@router.get(
    "/exceptions",
    response_model=DashboardExceptionsResponse,
    summary="Get exception analytics breakdown by severity, category, and recent records",
)
def get_dashboard_exceptions(
    merchant_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> DashboardExceptionsResponse:
    """Aggregates exception ticket volumes across categories and severities."""
    base_query = db.query(PaymentException)
    if merchant_id:
        base_query = base_query.join(
            ReconciliationResult, PaymentException.reconciliation_id == ReconciliationResult.id
        ).join(
            Transaction, ReconciliationResult.transaction_id == Transaction.id
        ).filter(Transaction.merchant_id == merchant_id)

    # 1. By Severity
    sev_rows = (
        db.query(PaymentException.severity, func.count(PaymentException.id))
        .group_by(PaymentException.severity)
        .all()
    )
    by_severity = [
        MetricCount(name=row[0].value if hasattr(row[0], "value") else str(row[0]), count=row[1])
        for row in sev_rows if row[0] is not None
    ]

    # 2. By Category
    cat_rows = (
        db.query(PaymentException.category, func.count(PaymentException.id))
        .group_by(PaymentException.category)
        .all()
    )
    by_category = [
        MetricCount(name=str(row[0]), count=row[1])
        for row in cat_rows if row[0] is not None
    ]

    # 3. Recent 10 exceptions
    recent_records = (
        base_query.order_by(PaymentException.created_at.desc())
        .limit(10)
        .all()
    )
    recent_items: List[RecentExceptionItem] = []
    for exc in recent_records:
        recon = exc.reconciliation_result
        diff = float(recon.difference_amount) if (recon and recon.difference_amount is not None) else None
        txn = recon.transaction if recon else None
        recent_items.append(
            RecentExceptionItem(
                id=exc.id,
                transaction_id=txn.id if txn else None,
                transaction_reference=txn.transaction_reference if txn else None,
                category=exc.category,
                severity=exc.severity.value if hasattr(exc.severity, "value") else str(exc.severity),
                status=exc.status.value if hasattr(exc.status, "value") else str(exc.status),
                difference_amount=diff,
                currency=txn.currency if txn else "INR",
                created_at=exc.created_at,
            )
        )

    total_count = sum(s.count for s in by_severity)

    return DashboardExceptionsResponse(
        total_exceptions=total_count,
        by_severity=by_severity,
        by_category=by_category,
        recent_exceptions=recent_items,
    )


@router.get(
    "/investigations",
    response_model=DashboardInvestigationsResponse,
    summary="Get AI investigation agent metrics, decisions, and recent investigations",
)
def get_dashboard_investigations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> DashboardInvestigationsResponse:
    """Returns AI Agent triage status, decision counts, and recent investigations."""
    query = db.query(AgentInvestigation)

    # Status counts
    total = query.count()
    completed = query.filter(AgentInvestigation.status == InvestigationStatus.completed).count()
    investigating = query.filter(AgentInvestigation.status == InvestigationStatus.investigating).count()
    failed = query.filter(AgentInvestigation.status == InvestigationStatus.failed).count()

    # Decision counts
    monitor_count = query.filter(AgentInvestigation.decision == AgentDecision.monitor).count()
    review_count = query.filter(AgentInvestigation.decision == AgentDecision.review).count()
    escalate_count = query.filter(AgentInvestigation.decision == AgentDecision.escalate).count()

    # Risk & Escalations
    escalations_count = query.filter(AgentInvestigation.escalation_required.is_(True)).count()
    critical_risk_count = query.filter(AgentInvestigation.risk_level == RiskLevel.critical).count()

    # Recent 10
    recent_records = query.order_by(AgentInvestigation.started_at.desc()).limit(10).all()
    recent_items = [
        RecentInvestigationItem(
            id=inv.id,
            exception_id=inv.exception_id,
            reconciliation_id=inv.reconciliation_id,
            investigation_type=inv.investigation_type,
            status=inv.status.value if hasattr(inv.status, "value") else str(inv.status),
            decision=inv.decision.value if hasattr(inv.decision, "value") else str(inv.decision),
            risk_level=inv.risk_level.value if hasattr(inv.risk_level, "value") else str(inv.risk_level),
            confidence_score=float(inv.confidence_score or 0),
            escalation_required=bool(inv.escalation_required),
            escalation_team=inv.escalation_team,
            summary=inv.summary or "",
            created_at=inv.started_at,
        )
        for inv in recent_records
    ]

    return DashboardInvestigationsResponse(
        total_investigations=total,
        completed=completed,
        investigating=investigating,
        failed=failed,
        monitor_count=monitor_count,
        review_count=review_count,
        escalate_count=escalate_count,
        escalations_count=escalations_count,
        critical_risk_count=critical_risk_count,
        recent_investigations=recent_items,
    )


@router.get(
    "/reconciliation-health",
    response_model=DashboardReconciliationHealthResponse,
    summary="Get reconciliation health distribution percentages across match statuses",
)
def get_reconciliation_health(
    merchant_id: Optional[uuid.UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> DashboardReconciliationHealthResponse:
    """Computes match status distribution for charts and health indicators."""
    query = db.query(ReconciliationResult.match_status, func.count(ReconciliationResult.id))
    if merchant_id:
        query = query.join(Transaction, ReconciliationResult.transaction_id == Transaction.id).filter(
            Transaction.merchant_id == merchant_id
        )

    rows = query.group_by(ReconciliationResult.match_status).all()
    status_counts = {
        row[0].value if hasattr(row[0], "value") else str(row[0]): row[1]
        for row in rows if row[0] is not None
    }

    total_evaluated = sum(status_counts.values())

    LABELS = {
        "matched": "Matched",
        "partial_match": "Partial Match",
        "amount_mismatch": "Amount Mismatch",
        "missing_in_bank": "Missing in Bank",
        "missing_in_gateway": "Missing in Gateway",
        "duplicate": "Duplicates",
        "delayed": "Delayed Settlement",
        "unresolved": "Unresolved",
    }

    statuses: List[ReconciliationHealthStatus] = []
    matched_count = status_counts.get("matched", 0) + status_counts.get("partial_match", 0)

    for key, label in LABELS.items():
        count = status_counts.get(key, 0)
        pct = round((count / total_evaluated * 100.0), 2) if total_evaluated > 0 else 0.0
        statuses.append(
            ReconciliationHealthStatus(
                status=key,
                label=label,
                count=count,
                percentage=pct,
            )
        )

    overall_rate = round((matched_count / total_evaluated * 100.0), 2) if total_evaluated > 0 else 0.0

    return DashboardReconciliationHealthResponse(
        total_evaluated=total_evaluated,
        reconciliation_rate=overall_rate,
        statuses=statuses,
    )
