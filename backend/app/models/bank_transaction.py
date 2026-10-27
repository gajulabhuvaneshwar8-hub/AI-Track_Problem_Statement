"""
app/models/bank_transaction.py

BankTransaction ORM model.
Represents a transaction as it appears on a bank statement.
Matched against gateway transactions during reconciliation.
No business logic — pure data definition only.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Index, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.reconciliation_result import ReconciliationResult


class BankTransaction(Base):
    """
    Bank statement transaction record.

    Money columns use Numeric(18, 4) — never Float.
    """

    __tablename__ = "bank_transactions"

    # ------------------------------------------------------------------
    # Composite indexes defined at table level
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_bank_transactions_bank_reference", "bank_reference"),
        Index("ix_bank_transactions_transaction_reference", "transaction_reference"),
        Index("ix_bank_transactions_transaction_date", "transaction_date"),
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
    # References
    # ------------------------------------------------------------------
    bank_reference: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    # Cross-reference to the gateway transaction_reference (denormalised for
    # fast lookup before reconciliation resolves the FK).
    transaction_reference: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )

    # ------------------------------------------------------------------
    # Financial data  (Numeric — never Float)
    # ------------------------------------------------------------------
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # ------------------------------------------------------------------
    # Transaction metadata
    # ------------------------------------------------------------------
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

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
    reconciliation_results: Mapped[List["ReconciliationResult"]] = relationship(
        "ReconciliationResult",
        back_populates="bank_transaction",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<BankTransaction bank_ref={self.bank_reference!r} "
            f"amount={self.amount} bank={self.bank_name!r}>"
        )
