"""
app/schemas/reconciliation.py

Pydantic schemas for reconciliation engine runs, results, and summary statistics.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ExceptionSeverity, ExceptionStatus, MatchStatus
from app.schemas.common import PaginatedResponse


class ReconciliationRunRequest(BaseModel):
    """Request payload to trigger a reconciliation run."""

    merchant_id: Optional[uuid.UUID] = Field(
        None, description="Optional merchant UUID to scope reconciliation"
    )


class ReconciliationSummaryResponse(BaseModel):
    """Aggregated reconciliation statistics."""

    total_gateway_transactions: int = 0
    total_bank_transactions: int = 0
    matched: int = 0
    partial_match: int = 0
    amount_mismatch: int = 0
    missing_in_bank: int = 0
    missing_in_gateway: int = 0
    duplicates: int = 0
    unresolved: int = 0
    delayed: int = 0
    total_expected_amount: Decimal = Decimal("0.0000")
    total_actual_amount: Decimal = Decimal("0.0000")
    total_difference: Decimal = Decimal("0.0000")
    reconciliation_accuracy: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ReconciliationRunResponse(BaseModel):
    """Response returned by POST /api/reconciliation/run."""

    status: str = "completed"
    summary: ReconciliationSummaryResponse


class ReconciliationResultResponse(BaseModel):
    """Single reconciliation match record."""

    id: uuid.UUID
    transaction_id: Optional[uuid.UUID] = None
    bank_transaction_id: Optional[uuid.UUID] = None
    match_status: MatchStatus
    confidence_score: Optional[Decimal] = None
    expected_amount: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    difference_amount: Optional[Decimal] = None
    matching_method: Optional[str] = None
    explanation: Optional[str] = None
    reconciled_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExceptionSummaryItem(BaseModel):
    """Brief exception representation for nested reconciliation detail."""

    id: uuid.UUID
    severity: ExceptionSeverity
    category: Optional[str] = None
    title: str
    status: ExceptionStatus

    model_config = ConfigDict(from_attributes=True)


class ReconciliationResultDetailResponse(ReconciliationResultResponse):
    """Detailed reconciliation result including related exceptions."""

    exceptions: List[ExceptionSummaryItem] = Field(default_factory=list)


PaginatedReconciliationResults = PaginatedResponse[ReconciliationResultResponse]
