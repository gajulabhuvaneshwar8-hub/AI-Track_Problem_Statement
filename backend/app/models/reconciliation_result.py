"""
app/models/reconciliation_result.py

ReconciliationResult ORM model.
Records the outcome of matching a gateway Transaction against a BankTransaction.
Stores confidence score, expected/actual amounts, and human-readable explanation.
No business logic — pure data definition only.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import MatchStatus

if TYPE_CHECKING:
    from app.models.agent_investigation import AgentInvestigation
    from app.models.ai_analysis import AIAnalysis
    from app.models.bank_transaction import BankTransaction
    from app.models.exception import PaymentException
    from app.models.transaction import Transaction


class ReconciliationResult(Base):
    """
    Outcome record for a single reconciliation match attempt.

    confidence_score: Numeric(5, 4) — value between 0.0000 and 1.0000.
    amount columns: Numeric(18, 4) — never Float.
    """

    __tablename__ = "reconciliation_results"

    # ------------------------------------------------------------------
    # Table-level indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_recon_results_transaction_id", "transaction_id"),
        Index("ix_recon_results_bank_transaction_id", "bank_transaction_id"),
        Index("ix_recon_results_match_status", "match_status"),
        Index("ix_recon_results_reconciled_at", "reconciled_at"),
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
    # Foreign keys (both nullable — result may reference only one side)
    # ------------------------------------------------------------------
    transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    bank_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("bank_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Match outcome
    # ------------------------------------------------------------------
    match_status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, name="matchstatus", create_type=True),
        nullable=False,
    )
    # Score between 0.0000 and 1.0000
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4), nullable=True
    )

    # ------------------------------------------------------------------
    # Amount comparison  (Numeric — never Float)
    # ------------------------------------------------------------------
    expected_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 4), nullable=True
    )
    actual_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 4), nullable=True
    )
    difference_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 4), nullable=True
    )

    # ------------------------------------------------------------------
    # Matching metadata
    # ------------------------------------------------------------------
    matching_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Timestamps
    # ------------------------------------------------------------------
    reconciled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    transaction: Mapped[Optional["Transaction"]] = relationship(
        "Transaction",
        back_populates="reconciliation_results",
        lazy="select",
    )
    bank_transaction: Mapped[Optional["BankTransaction"]] = relationship(
        "BankTransaction",
        back_populates="reconciliation_results",
        lazy="select",
    )
    exceptions: Mapped[List["PaymentException"]] = relationship(
        "PaymentException",
        back_populates="reconciliation_result",
        cascade="all, delete-orphan",
        lazy="select",
    )
    ai_analyses: Mapped[List["AIAnalysis"]] = relationship(
        "AIAnalysis",
        back_populates="reconciliation_result",
        cascade="all, delete-orphan",
        lazy="select",
    )
    agent_investigations: Mapped[List["AgentInvestigation"]] = relationship(
        "AgentInvestigation",
        back_populates="reconciliation_result",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ReconciliationResult id={self.id} "
            f"status={self.match_status} score={self.confidence_score}>"
        )
