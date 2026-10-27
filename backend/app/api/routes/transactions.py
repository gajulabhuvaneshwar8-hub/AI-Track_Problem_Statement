"""
app/api/routes/transactions.py

CRUD endpoints for Transaction with rich filtering and pagination.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_current_user
from app.models.enums import TransactionSource, TransactionStatus
from app.models.user import User
from app.schemas.transaction import (
    PaginatedTransactions,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.services import transaction_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new transaction",
)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> TransactionResponse:
    try:
        return transaction_service.create_transaction(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "",
    response_model=PaginatedTransactions,
    summary="List transactions with optional filters and pagination",
)
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    merchant_id: Optional[uuid.UUID] = Query(None),
    status: Optional[TransactionStatus] = Query(None),
    source: Optional[TransactionSource] = Query(None),
    gateway: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> PaginatedTransactions:
    skip = (page - 1) * page_size
    items, total = transaction_service.list_transactions(
        db,
        merchant_id=merchant_id,
        status=status,
        source=source,
        gateway=gateway,
        payment_method=payment_method,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=page_size,
    )
    return PaginatedTransactions(items=items, page=page, page_size=page_size, total=total)


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get a single transaction by ID",
)
def get_transaction(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> TransactionResponse:
    txn = transaction_service.get_transaction(db, transaction_id)
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return txn


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Update a transaction",
)
def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> TransactionResponse:
    txn = transaction_service.update_transaction(db, transaction_id, payload)
    if not txn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return txn


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a transaction",
)
def delete_transaction(
    transaction_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> Response:
    deleted = transaction_service.delete_transaction(db, transaction_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
