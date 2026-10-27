"""
app/services/bank_transaction_service.py

Database operations for the BankTransaction entity.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.bank_transaction import BankTransaction
from app.schemas.bank_transaction import BankTransactionCreate, BankTransactionUpdate

logger = logging.getLogger(__name__)


def create_bank_transaction(
    db: Session, payload: BankTransactionCreate
) -> BankTransaction:
    """Create a bank transaction. Raises ValueError on duplicate bank_reference."""
    existing = (
        db.query(BankTransaction)
        .filter(BankTransaction.bank_reference == payload.bank_reference)
        .first()
    )
    if existing:
        raise ValueError(
            f"bank_reference '{payload.bank_reference}' already exists"
        )

    bt = BankTransaction(id=uuid.uuid4(), **payload.model_dump())
    db.add(bt)
    db.commit()
    db.refresh(bt)
    logger.info("Created bank transaction %s ref=%s", bt.id, bt.bank_reference)
    return bt


def get_bank_transaction(
    db: Session, bank_transaction_id: uuid.UUID
) -> Optional[BankTransaction]:
    return db.get(BankTransaction, bank_transaction_id)


def list_bank_transactions(
    db: Session,
    *,
    bank_name: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[BankTransaction], int]:
    query = db.query(BankTransaction)

    if bank_name is not None:
        query = query.filter(BankTransaction.bank_name.ilike(f"%{bank_name}%"))
    if status is not None:
        query = query.filter(BankTransaction.status == status)
    if date_from is not None:
        query = query.filter(BankTransaction.transaction_date >= date_from)
    if date_to is not None:
        query = query.filter(BankTransaction.transaction_date <= date_to)

    total = query.count()
    items = (
        query.order_by(BankTransaction.transaction_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def update_bank_transaction(
    db: Session,
    bank_transaction_id: uuid.UUID,
    payload: BankTransactionUpdate,
) -> Optional[BankTransaction]:
    bt = get_bank_transaction(db, bank_transaction_id)
    if not bt:
        return None
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(bt, field, value)
    db.commit()
    db.refresh(bt)
    return bt


def delete_bank_transaction(
    db: Session, bank_transaction_id: uuid.UUID
) -> bool:
    bt = get_bank_transaction(db, bank_transaction_id)
    if not bt:
        return False
    db.delete(bt)
    db.commit()
    return True
