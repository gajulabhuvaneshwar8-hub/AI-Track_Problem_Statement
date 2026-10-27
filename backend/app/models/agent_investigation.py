"""
app/models/agent_investigation.py

AgentInvestigation ORM model for Step 7.
Stores automated exception investigations conducted by the AI Reconciliation Investigation Agent.
Captures confirmed facts, possible causes, root cause, financial impact, recommended actions,
deterministic decisions (MONITOR, REVIEW, ESCALATE), risk levels, and collected evidence.

DOES NOT modify reconciliation decisions, transaction amounts, refunds, or financial records.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, JSON, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import AgentDecision, InvestigationStatus, RiskLevel

if TYPE_CHECKING:
    from app.models.exception import PaymentException
    from app.models.reconciliation_result import ReconciliationResult


class AgentInvestigation(Base):
    """
    Automated investigation record produced by the AI Reconciliation Investigation Agent.
    """

    __tablename__ = "agent_investigations"

    # ------------------------------------------------------------------
    # Table-level indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_agent_inv_reconciliation_id", "reconciliation_id"),
        Index("ix_agent_inv_exception_id", "exception_id"),
        Index("ix_agent_inv_status", "status"),
        Index("ix_agent_inv_decision", "decision"),
        Index("ix_agent_inv_risk_level", "risk_level"),
        Index("ix_agent_inv_created_at", "created_at"),
    )

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Foreign keys
    # ------------------------------------------------------------------
    reconciliation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reconciliation_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    exception_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("exceptions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Status & Classification
    # ------------------------------------------------------------------
    status: Mapped[InvestigationStatus] = mapped_column(
        Enum(InvestigationStatus, name="investigationstatus", create_type=True),
        nullable=False,
        default=InvestigationStatus.pending,
        server_default=InvestigationStatus.pending.value,
    )
    investigation_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="general_investigation",
    )

    # ------------------------------------------------------------------
    # Investigation Findings
    # ------------------------------------------------------------------
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    confirmed_facts: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    possible_causes: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    impact: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Decision Engine Outcomes
    # ------------------------------------------------------------------
    decision: Mapped[AgentDecision] = mapped_column(
        Enum(AgentDecision, name="agentdecision", create_type=True),
        nullable=False,
        default=AgentDecision.review,
        server_default=AgentDecision.review.value,
    )
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risklevel", create_type=True),
        nullable=False,
        default=RiskLevel.medium,
        server_default=RiskLevel.medium.value,
    )
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True,
    )
    escalation_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    escalation_team: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Structured Evidence
    # ------------------------------------------------------------------
    evidence: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    reconciliation_result: Mapped[Optional["ReconciliationResult"]] = relationship(
        "ReconciliationResult",
        back_populates="agent_investigations",
        lazy="select",
    )
    exception: Mapped[Optional["PaymentException"]] = relationship(
        "PaymentException",
        back_populates="agent_investigations",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AgentInvestigation id={self.id} status={self.status.value} "
            f"decision={self.decision.value} risk={self.risk_level.value}>"
        )
