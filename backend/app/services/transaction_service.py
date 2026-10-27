"""
app/services/transaction_service.py

Database operations for the Transaction entity.
Supports rich filtering for the reconciliation workflow.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.enums import TransactionSource, TransactionStatus
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate

logger = logging.getLogger(__name__)


def create_transaction(db: Session, payload: TransactionCreate) -> Transaction:
    """Create and persist a Transaction. Raises ValueError on duplicate reference."""
    existing = (
        db.query(Transaction)
        .filter(Transaction.transaction_reference == payload.transaction_reference)
        .first()
    )
    if existing:
        raise ValueError(
            f"transaction_reference '{payload.transaction_reference}' already exists"
        )

    txn = Transaction(
        id=uuid.uuid4(),
        **payload.model_dump(),
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    logger.info("Created transaction %s ref=%s", txn.id, txn.transaction_reference)
    return txn


def get_transaction(db: Session, transaction_id: uuid.UUID) -> Optional[Transaction]:
    return db.get(Transaction, transaction_id)


def list_transactions(
    db: Session,
    *,
    merchant_id: Optional[uuid.UUID] = None,
    status: Optional[TransactionStatus] = None,
    source: Optional[TransactionSource] = None,
    gateway: Optional[str] = None,
    payment_method: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[Transaction], int]:
    """Return (items, total) with optional filters and pagination."""
    query = db.query(Transaction)

    if merchant_id is not None:
        query = query.filter(Transaction.merchant_id == merchant_id)
    if status is not None:
        query = query.filter(Transaction.status == status)
    if source is not None:
        query = query.filter(Transaction.source == source)
    if gateway is not None:
        query = query.filter(Transaction.gateway.ilike(f"%{gateway}%"))
    if payment_method is not None:
        query = query.filter(Transaction.payment_method.ilike(f"%{payment_method}%"))
    if date_from is not None:
        query = query.filter(Transaction.transaction_date >= date_from)
    if date_to is not None:
        query = query.filter(Transaction.transaction_date <= date_to)

    total = query.count()
    items = (
        query.order_by(Transaction.transaction_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def update_transaction(
    db: Session,
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
) -> Optional[Transaction]:
    txn = get_transaction(db, transaction_id)
    if not txn:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(txn, field, value)
    db.commit()
    db.refresh(txn)
    return txn


def delete_transaction(db: Session, transaction_id: uuid.UUID) -> bool:
    txn = get_transaction(db, transaction_id)
    if not txn:
        return False
    db.delete(txn)
    db.commit()
    return True
