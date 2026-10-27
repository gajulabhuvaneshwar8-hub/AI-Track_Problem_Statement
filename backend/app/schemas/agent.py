"""
app/schemas/agent.py

Pydantic schemas for the AI Reconciliation Investigation Agent (Step 7).
Defines request and response structures for investigations, evidence items,
escalation recommendations, and paginated investigation lists.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AgentDecision, InvestigationStatus, RiskLevel


class EvidenceItem(BaseModel):
    """
    Structured piece of evidence gathered by EvidenceCollector.
    """

    source: str = Field(..., description="Ledger / data source (e.g. gateway, bank, settlement, reconciliation, exception)")
    field: str = Field(..., description="Data field name")
    value: Any = Field(..., description="Observed value")
    reliability: float = Field(..., ge=0.0, le=1.0, description="Reliability confidence between 0.0 and 1.0")


class InvestigationStartRequest(BaseModel):
    """Payload for starting an investigation (optional body)."""

    force: bool = Field(False, description="Re-run investigation even if already completed")


class EscalationResponse(BaseModel):
    """
    Escalation recommendation details.
    """

    action: str = Field("ESCALATE", description="Escalation action directive")
    priority: str = Field(..., description="Priority level: CRITICAL, HIGH, MEDIUM, LOW")
    reason: str = Field(..., description="Clear rationale explaining the escalation")
    recommended_team: str = Field(..., description="Assigned operations team")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentInvestigationResponse(BaseModel):
    """
    Complete structured investigation response conforming to Step 7/8 specs.
    """

    investigation_id: uuid.UUID = Field(..., alias="id")
    reconciliation_id: Optional[uuid.UUID] = None
    exception_id: Optional[uuid.UUID] = None
    status: InvestigationStatus
    investigation_type: str
    summary: str
    confirmed_facts: List[str]
    possible_causes: List[str]
    root_cause: Optional[str] = None
    impact: Dict[str, Any]
    risk_level: RiskLevel
    recommended_action: Optional[str] = None
    decision: AgentDecision
    escalation_required: bool
    escalation_team: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    evidence: List[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PaginatedAgentInvestigations(BaseModel):
    """Paginated list of investigation results."""

    items: List[AgentInvestigationResponse]
    page: int
    page_size: int
    total: int
