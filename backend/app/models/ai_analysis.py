"""
app/models/ai_analysis.py

AIAnalysis ORM model.
Stores interpretive AI and fallback analyses of reconciliation results and exceptions.
Provides root cause analysis, human-readable explanations, risk levels, and recommendations.
Does NOT modify or override reconciliation results or transaction records.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import AnalysisStatus, AnalysisType, RiskLevel

if TYPE_CHECKING:
    from app.models.exception import PaymentException
    from app.models.reconciliation_result import ReconciliationResult


class AIAnalysis(Base):
    """
    AI analysis record for a reconciliation result or exception ticket.
    """

    __tablename__ = "ai_analyses"

    # ------------------------------------------------------------------
    # Table-level indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_ai_analyses_reconciliation_id", "reconciliation_id"),
        Index("ix_ai_analyses_exception_id", "exception_id"),
        Index("ix_ai_analyses_analysis_type", "analysis_type"),
        Index("ix_ai_analyses_risk_level", "risk_level"),
        Index("ix_ai_analyses_status", "status"),
        Index("ix_ai_analyses_created_at", "created_at"),
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
    # Foreign keys (nullable: can target a reconciliation, an exception, or both)
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
    # Classification & Content
    # ------------------------------------------------------------------
    analysis_type: Mapped[AnalysisType] = mapped_column(
        Enum(AnalysisType, name="analysistype", create_type=True),
        nullable=False,
        default=AnalysisType.exception_analysis,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risklevel", create_type=True),
        nullable=False,
        default=RiskLevel.medium,
    )
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4), nullable=True
    )

    # ------------------------------------------------------------------
    # Provider & Execution Details
    # ------------------------------------------------------------------
    ai_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus, name="analysisstatus", create_type=True),
        nullable=False,
        default=AnalysisStatus.completed,
    )
    raw_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
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
        back_populates="ai_analyses",
        lazy="select",
    )
    exception: Mapped[Optional["PaymentException"]] = relationship(
        "PaymentException",
        back_populates="ai_analyses",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AIAnalysis id={self.id} type={self.analysis_type} "
            f"risk={self.risk_level} status={self.status}>"
        )
