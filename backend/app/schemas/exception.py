"""
app/schemas/exception.py

Pydantic schemas for reconciliation exception management and human-in-the-loop workflows.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import ExceptionSeverity, ExceptionStatus
from app.schemas.common import PaginatedResponse


class ExceptionCreate(BaseModel):
    reconciliation_id: Optional[uuid.UUID] = None
    merchant_id: Optional[uuid.UUID] = None
    severity: ExceptionSeverity
    category: Optional[str] = Field(None, max_length=100)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    recommended_action: Optional[str] = None
    status: ExceptionStatus = ExceptionStatus.open
    assigned_to: Optional[uuid.UUID] = None


class ExceptionUpdate(BaseModel):
    severity: Optional[ExceptionSeverity] = None
    category: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    recommended_action: Optional[str] = None
    status: Optional[ExceptionStatus] = None
    assigned_to: Optional[uuid.UUID] = None
    resolution_note: Optional[str] = None
    reviewer_note: Optional[str] = None


class ExceptionAssignRequest(BaseModel):
    assigned_to: Optional[uuid.UUID] = Field(None, description="User ID to assign, or null to unassign")


class ExceptionStatusRequest(BaseModel):
    status: ExceptionStatus = Field(..., description="Target status (e.g. investigating)")
    note: Optional[str] = Field(None, description="Optional note describing reason for status update")


class ExceptionReviewRequest(BaseModel):
    note: str = Field(..., min_length=1, description="Human review note or finding")


class ExceptionResolveRequest(BaseModel):
    resolution_note: str = Field(..., min_length=1, description="Mandatory explanation of resolution")


class ExceptionIgnoreRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="Mandatory explanation for ignoring exception")


class ExceptionEscalateRequest(BaseModel):
    reason: str = Field(..., min_length=1, description="Mandatory escalation rationale")
    suggested_team: Optional[str] = Field(None, description="Target operational or engineering team")


class ExceptionReopenRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Reason for reopening resolved or ignored exception")


class TimelineEvent(BaseModel):
    id: str
    event_type: str
    title: str
    description: Optional[str] = None
    actor: Optional[str] = None
    actor_role: Optional[str] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class ExceptionTimelineResponse(BaseModel):
    exception_id: uuid.UUID
    events: List[TimelineEvent]


class ExceptionWorkflowSummary(BaseModel):
    total: int = 0
    open: int = 0
    investigating: int = 0
    resolved: int = 0
    ignored: int = 0
    critical: int = 0
    unassigned: int = 0
    resolved_today: int = 0
    escalated: int = 0


class ExceptionResponse(BaseModel):
    id: uuid.UUID
    reconciliation_id: Optional[uuid.UUID] = None
    merchant_id: Optional[uuid.UUID] = None
    severity: ExceptionSeverity
    category: Optional[str] = None
    title: str
    description: Optional[str] = None
    recommended_action: Optional[str] = None
    status: ExceptionStatus
    assigned_to: Optional[uuid.UUID] = None
    assignee_name: Optional[str] = None
    resolved_by: Optional[uuid.UUID] = None
    ignored_by: Optional[uuid.UUID] = None
    resolution_note: Optional[str] = None
    reviewer_note: Optional[str] = None
    escalation_reason: Optional[str] = None
    resolved_at: Optional[datetime] = None
    ignored_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_at: datetime
    amount: Optional[Decimal] = None
    currency: Optional[str] = "INR"

    model_config = {"from_attributes": True}


class ExceptionDetailedResponse(BaseModel):
    exception: ExceptionResponse
    transaction: Optional[Dict[str, Any]] = None
    bank_transaction: Optional[Dict[str, Any]] = None
    reconciliation: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    agent_investigation: Optional[Dict[str, Any]] = None
    assignee: Optional[Dict[str, Any]] = None


PaginatedExceptions = PaginatedResponse[ExceptionResponse]
