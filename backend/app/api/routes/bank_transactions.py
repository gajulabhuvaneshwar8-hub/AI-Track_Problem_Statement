"""
app/api/routes/bank_transactions.py

CRUD endpoints for BankTransaction with filtering and pagination.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_current_user
from app.models.user import User
from app.schemas.bank_transaction import (
    BankTransactionCreate,
    BankTransactionResponse,
    BankTransactionUpdate,
    PaginatedBankTransactions,
)
from app.services import bank_transaction_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/bank-transactions", tags=["Bank Transactions"])


@router.post(
    "",
    response_model=BankTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new bank statement transaction",
)
def create_bank_transaction(
    payload: BankTransactionCreate,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> BankTransactionResponse:
    try:
        return bank_transaction_service.create_bank_transaction(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "",
    response_model=PaginatedBankTransactions,
    summary="List bank transactions with optional filters",
)
def list_bank_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    bank_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> PaginatedBankTransactions:
    skip = (page - 1) * page_size
    items, total = bank_transaction_service.list_bank_transactions(
        db,
        bank_name=bank_name,
        status=status,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=page_size,
    )
    return PaginatedBankTransactions(items=items, page=page, page_size=page_size, total=total)


@router.get(
    "/{bank_transaction_id}",
    response_model=BankTransactionResponse,
    summary="Get a single bank transaction by ID",
)
def get_bank_transaction(
    bank_transaction_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> BankTransactionResponse:
    bt = bank_transaction_service.get_bank_transaction(db, bank_transaction_id)
    if not bt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bank transaction not found"
        )
    return bt


@router.put(
    "/{bank_transaction_id}",
    response_model=BankTransactionResponse,
    summary="Update a bank transaction",
)
def update_bank_transaction(
    bank_transaction_id: uuid.UUID,
    payload: BankTransactionUpdate,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> BankTransactionResponse:
    bt = bank_transaction_service.update_bank_transaction(db, bank_transaction_id, payload)
    if not bt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bank transaction not found"
        )
    return bt


@router.delete(
    "/{bank_transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a bank transaction",
)
def delete_bank_transaction(
    bank_transaction_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> Response:
    deleted = bank_transaction_service.delete_bank_transaction(db, bank_transaction_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bank transaction not found"
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
