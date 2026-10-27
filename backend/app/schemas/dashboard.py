"""
app/schemas/dashboard.py

Pydantic schemas for aggregated dashboard statistics, reconciliation health,
exception overviews, and AI agent investigation metrics.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DashboardSummaryResponse(BaseModel):
    """Core KPI metrics for the Finance Operations Control Center top bar."""
    total_transactions: int = Field(..., description="Total gateway transactions in system")
    matched_transactions: int = Field(..., description="Transactions fully or partially matched")
    exceptions_count: int = Field(..., description="Total active payment exceptions")
    reconciliation_rate: float = Field(..., description="Percentage of transactions successfully reconciled (0.0 - 100.0)")
    amount_reconciled: float = Field(..., description="Total monetary value reconciled")
    critical_issues: int = Field(..., description="Count of critical severity exceptions")

    model_config = ConfigDict(from_attributes=True)


class MetricCount(BaseModel):
    name: str
    count: int
    percentage: Optional[float] = None


class RecentExceptionItem(BaseModel):
    id: uuid.UUID
    transaction_id: Optional[uuid.UUID] = None
    transaction_reference: Optional[str] = None
    category: str
    severity: str
    status: str
    difference_amount: Optional[float] = None
    currency: Optional[str] = "INR"
    created_at: datetime


class DashboardExceptionsResponse(BaseModel):
    """Exception metrics breakdown by severity, category, and recent items."""
    total_exceptions: int
    by_severity: List[MetricCount]
    by_category: List[MetricCount]
    recent_exceptions: List[RecentExceptionItem]


class RecentInvestigationItem(BaseModel):
    id: uuid.UUID
    exception_id: Optional[uuid.UUID] = None
    reconciliation_id: Optional[uuid.UUID] = None
    investigation_type: str
    status: str
    decision: str
    risk_level: str
    confidence_score: float
    escalation_required: bool
    escalation_team: Optional[str] = None
    summary: str
    created_at: datetime


class DashboardInvestigationsResponse(BaseModel):
    """AI Agent investigation overview for control center triage."""
    total_investigations: int
    completed: int
    investigating: int
    failed: int
    monitor_count: int
    review_count: int
    escalate_count: int
    escalations_count: int
    critical_risk_count: int
    recent_investigations: List[RecentInvestigationItem]


class ReconciliationHealthStatus(BaseModel):
    status: str
    label: str
    count: int
    percentage: float


class DashboardReconciliationHealthResponse(BaseModel):
    """Reconciliation health status distribution."""
    total_evaluated: int
    reconciliation_rate: float
    statuses: List[ReconciliationHealthStatus]
