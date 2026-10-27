"""
app/schemas/ai_analysis.py

Pydantic schemas for AI reconciliation exception analysis, root causes,
investigations, and recommendations.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.enums import AnalysisStatus, AnalysisType, RiskLevel


class AIAnalysisRequest(BaseModel):
    """Payload for triggering an AI analysis."""

    force: bool = Field(
        default=False,
        description="Force a fresh analysis even if an identical one already exists",
    )
    analysis_type: Optional[AnalysisType] = Field(
        default=AnalysisType.exception_analysis,
        description="Type of analysis to conduct",
    )


class AIAnalysisResponse(BaseModel):
    """Standard response model for an AI or fallback analysis."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    reconciliation_id: Optional[uuid.UUID] = None
    exception_id: Optional[uuid.UUID] = None
    analysis_type: AnalysisType
    summary: str
    root_cause: Optional[str] = None
    impact: Optional[str] = None
    recommended_action: Optional[str] = None
    risk_level: RiskLevel
    confidence_score: Optional[Decimal] = None
    ai_provider: str
    model_name: str
    status: AnalysisStatus
    raw_response: Optional[str] = None
    created_at: datetime

    @computed_field
    @property
    def analysis_id(self) -> uuid.UUID:
        """Alias for id to support response format requirement."""
        return self.id


class AIAnalysisListResponse(BaseModel):
    """Paginated list of AI analysis records."""

    items: List[AIAnalysisResponse]
    total: int
    page: int
    page_size: int


class AIInvestigationFinding(BaseModel):
    """Key diagnostic finding in an investigation."""

    area: str
    finding: str
    severity: str


class AIInvestigationResponse(BaseModel):
    """Deep investigation response model."""

    analysis: AIAnalysisResponse
    investigation_depth: str = "comprehensive"
    discrepancy_factors: List[str] = Field(default_factory=list)
    suggested_audit_steps: List[str] = Field(default_factory=list)
    human_action_required: bool = True
