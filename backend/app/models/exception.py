"""
app/models/exception.py

PaymentException ORM model.
Tracks reconciliation exceptions that require human or AI review.

Named PaymentException (not Exception) to avoid shadowing Python's
built-in Exception class.
No business logic — pure data definition only.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import ExceptionSeverity, ExceptionStatus

if TYPE_CHECKING:
    from app.models.agent_investigation import AgentInvestigation
    from app.models.ai_analysis import AIAnalysis
    from app.models.merchant import Merchant
    from app.models.reconciliation_result import ReconciliationResult
    from app.models.user import User


class PaymentException(Base):
    """
    Reconciliation exception ticket.

    Raised when a ReconciliationResult requires investigation.
    assigned_to is a nullable FK to users — supports both unassigned and
    assigned states.
    """

    __tablename__ = "exceptions"

    # ------------------------------------------------------------------
    # Table-level indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_exceptions_reconciliation_id", "reconciliation_id"),
        Index("ix_exceptions_status", "status"),
        Index("ix_exceptions_severity", "severity"),
        Index("ix_exceptions_assigned_to", "assigned_to"),
        Index("ix_exceptions_merchant_id", "merchant_id"),
        Index("ix_exceptions_created_at", "created_at"),
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
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    ignored_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    severity: Mapped[ExceptionSeverity] = mapped_column(
        Enum(ExceptionSeverity, name="exceptionseverity", create_type=True),
        nullable=False,
    )
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ------------------------------------------------------------------
    # Description
    # ------------------------------------------------------------------
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Workflow notes
    # ------------------------------------------------------------------
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewer_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    escalation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Workflow status
    # ------------------------------------------------------------------
    status: Mapped[ExceptionStatus] = mapped_column(
        Enum(ExceptionStatus, name="exceptionstatus", create_type=True),
        nullable=False,
        default=ExceptionStatus.open,
        server_default=ExceptionStatus.open.value,
    )

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ignored_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    escalated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
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
        back_populates="exceptions",
        lazy="select",
    )
    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_to],
        back_populates="assigned_exceptions",
        lazy="select",
    )
    resolver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[resolved_by],
        lazy="select",
    )
    ignorer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[ignored_by],
        lazy="select",
    )
    merchant: Mapped[Optional["Merchant"]] = relationship(
        "Merchant",
        foreign_keys=[merchant_id],
        lazy="select",
    )
    ai_analyses: Mapped[List["AIAnalysis"]] = relationship(
        "AIAnalysis",
        back_populates="exception",
        cascade="all, delete-orphan",
        lazy="select",
    )
    agent_investigations: Mapped[List["AgentInvestigation"]] = relationship(
        "AgentInvestigation",
        back_populates="exception",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<PaymentException id={self.id} "
            f"severity={self.severity} status={self.status} title={self.title!r}>"
        )

