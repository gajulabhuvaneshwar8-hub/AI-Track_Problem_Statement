"""
app/api/routes/reconciliation.py

Production reconciliation API endpoints.
Provides endpoints to trigger reconciliation runs, inspect match results,
fetch individual result details, and view summary metrics.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, require_finance_or_admin
from app.models.enums import MatchStatus
from app.models.merchant import Merchant
from app.models.user import User
from app.schemas.reconciliation import (
    PaginatedReconciliationResults,
    ReconciliationResultDetailResponse,
    ReconciliationResultResponse,
    ReconciliationRunRequest,
    ReconciliationRunResponse,
    ReconciliationSummaryResponse,
)
from app.services.reconciliation.reconciliation_service import ReconciliationService

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])


def _verify_merchant(merchant_id: Optional[uuid.UUID], db: Session) -> None:
    """Verify merchant exists in database if merchant_id is provided."""
    if merchant_id is not None:
        merchant = db.get(Merchant, merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Merchant with ID '{merchant_id}' not found.",
            )


@router.post(
    "/run",
    response_model=ReconciliationRunResponse,
    summary="Trigger a deterministic reconciliation run",
)
def run_reconciliation(
    payload: Optional[ReconciliationRunRequest] = None,
    current_user: User = Depends(require_finance_or_admin),
    db: Session = Depends(get_db_session),
) -> ReconciliationRunResponse:
    """
    Execute the core matching engine comparing gateway transactions and bank statements.
    Idempotent: updates existing results without creating duplicates.
    """
    merchant_id = payload.merchant_id if payload else None
    _verify_merchant(merchant_id, db)

    summary = ReconciliationService.run_reconciliation(merchant_id=merchant_id, db=db)
    return ReconciliationRunResponse(status="completed", summary=summary)


@router.get(
    "/results",
    response_model=PaginatedReconciliationResults,
    summary="List reconciliation results with filtering and pagination",
)
def list_reconciliation_results(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    merchant_id: Optional[uuid.UUID] = Query(None, description="Filter by merchant UUID"),
    match_status: Optional[MatchStatus] = Query(None, description="Filter by match status"),
    min_confidence: Optional[Decimal] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    max_confidence: Optional[Decimal] = Query(None, ge=0.0, le=1.0, description="Maximum confidence score"),
    date_from: Optional[datetime] = Query(None, description="Filter results reconciled after date"),
    date_to: Optional[datetime] = Query(None, description="Filter results reconciled before date"),
    current_user: User = Depends(require_finance_or_admin),
    db: Session = Depends(get_db_session),
) -> PaginatedReconciliationResults:
    """Retrieve paginated reconciliation outcome records."""
    _verify_merchant(merchant_id, db)

    items, total = ReconciliationService.get_results(
        db=db,
        page=page,
        page_size=page_size,
        merchant_id=merchant_id,
        match_status=match_status,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        date_from=date_from,
        date_to=date_to,
    )

    result_items = [ReconciliationResultResponse.model_validate(r) for r in items]
    return PaginatedReconciliationResults(
        items=result_items,
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/summary/{merchant_id}",
    response_model=ReconciliationSummaryResponse,
    summary="Get reconciliation summary statistics for a merchant",
)
def get_reconciliation_summary(
    merchant_id: uuid.UUID,
    current_user: User = Depends(require_finance_or_admin),
    db: Session = Depends(get_db_session),
) -> ReconciliationSummaryResponse:
    """Retrieve aggregated reconciliation metrics for a specific merchant."""
    _verify_merchant(merchant_id, db)
    return ReconciliationService.get_summary(merchant_id=merchant_id, db=db)


@router.get(
    "/results/{result_id}",
    response_model=ReconciliationResultDetailResponse,
    summary="Get a single reconciliation result by ID",
)
def get_reconciliation_result(
    result_id: uuid.UUID,
    current_user: User = Depends(require_finance_or_admin),
    db: Session = Depends(get_db_session),
) -> ReconciliationResultDetailResponse:
    """Fetch complete details and linked exceptions for a single reconciliation record."""
    result = ReconciliationService.get_result_by_id(result_id, db)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reconciliation result not found",
        )
    return ReconciliationResultDetailResponse.model_validate(result)
