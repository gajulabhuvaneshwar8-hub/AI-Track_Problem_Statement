"""
app/services/agents/agent_tools.py

Safe, read-only tools for the AI Reconciliation Investigation Agent.
Enforces read-only access to ledger records, settlements, and history.

STRICT INVARIANT:
The agent MUST NEVER have tools capable of:
  - modifying transaction amounts
  - modifying reconciliation decisions
  - issuing refunds
  - modifying settlements
  - deleting records
  - transferring money
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis
from app.models.bank_transaction import BankTransaction
from app.models.exception import PaymentException
from app.models.reconciliation_result import ReconciliationResult
from app.models.settlement import Settlement
from app.models.transaction import Transaction


def get_transaction(db: Session, transaction_id: uuid.UUID) -> Optional[Transaction]:
    """Read-only: fetches a gateway transaction by ID."""
    return db.get(Transaction, transaction_id)


def get_bank_transaction(db: Session, bank_transaction_id: uuid.UUID) -> Optional[BankTransaction]:
    """Read-only: fetches a bank statement transaction by ID."""
    return db.get(BankTransaction, bank_transaction_id)


def get_reconciliation_result(db: Session, reconciliation_id: uuid.UUID) -> Optional[ReconciliationResult]:
    """Read-only: fetches a reconciliation outcome record by ID."""
    return db.get(ReconciliationResult, reconciliation_id)


def get_settlement(
    db: Session,
    merchant_id: Optional[uuid.UUID],
    transaction_date: Optional[datetime],
) -> Optional[Settlement]:
    """
    Read-only: fetches settlement batch for merchant closest to transaction date.
    Searches within a window around transaction_date.
    """
    if not merchant_id:
        return None

    query = select(Settlement).where(Settlement.merchant_id == merchant_id)
    if transaction_date:
        # Search settlements on or shortly after the transaction date
        query = query.order_by(
            Settlement.settlement_date.desc()
        )
    return db.scalars(query).first()


def get_related_transactions(
    db: Session,
    transaction_reference: Optional[str],
    order_reference: Optional[str] = None,
    exclude_id: Optional[uuid.UUID] = None,
) -> List[Transaction]:
    """
    Read-only: finds related or duplicate transactions sharing reference or order reference.
    """
    if not transaction_reference and not order_reference:
        return []

    conditions = []
    if transaction_reference:
        conditions.append(Transaction.transaction_reference == transaction_reference)
    if order_reference:
        conditions.append(Transaction.order_reference == order_reference)

    stmt = select(Transaction).where(or_(*conditions))
    if exclude_id:
        stmt = stmt.where(Transaction.id != exclude_id)

    return list(db.scalars(stmt).all())


def get_related_exceptions(
    db: Session,
    transaction_id: Optional[uuid.UUID] = None,
    reconciliation_id: Optional[uuid.UUID] = None,
    exclude_id: Optional[uuid.UUID] = None,
) -> List[PaymentException]:
    """
    Read-only: finds prior exceptions linked to the same reconciliation or transaction.
    """
    stmt = select(PaymentException)
    conditions = []
    if reconciliation_id:
        conditions.append(PaymentException.reconciliation_id == reconciliation_id)
    if not conditions:
        return []

    stmt = stmt.where(or_(*conditions))
    if exclude_id:
        stmt = stmt.where(PaymentException.id != exclude_id)

    return list(db.scalars(stmt.order_by(PaymentException.created_at.desc())).all())


def get_previous_ai_analyses(
    db: Session,
    reconciliation_id: Optional[uuid.UUID] = None,
    exception_id: Optional[uuid.UUID] = None,
) -> List[AIAnalysis]:
    """
    Read-only: fetches prior AI analysis records for this reconciliation or exception.
    """
    conditions = []
    if reconciliation_id:
        conditions.append(AIAnalysis.reconciliation_id == reconciliation_id)
    if exception_id:
        conditions.append(AIAnalysis.exception_id == exception_id)

    if not conditions:
        return []

    stmt = select(AIAnalysis).where(or_(*conditions)).order_by(AIAnalysis.created_at.desc())
    return list(db.scalars(stmt).all())


def calculate_amount_difference(
    expected: Optional[Decimal],
    actual: Optional[Decimal],
) -> Decimal:
    """Read-only: calculates absolute discrepancy between expected and actual amounts."""
    exp = expected if expected is not None else Decimal("0")
    act = actual if actual is not None else Decimal("0")
    return abs(exp - act)


def calculate_delay_days(
    gateway_date: Optional[datetime],
    bank_date: Optional[datetime],
) -> Optional[int]:
    """Read-only: calculates days elapsed between gateway authorization and bank posting."""
    if not gateway_date or not bank_date:
        return None
    # Normalize naive/aware
    d1 = gateway_date.date() if isinstance(gateway_date, datetime) else gateway_date
    d2 = bank_date.date() if isinstance(bank_date, datetime) else bank_date
    return abs((d2 - d1).days)
