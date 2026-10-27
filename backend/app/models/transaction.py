"""
app/models/transaction.py

Transaction ORM model.
Represents a payment transaction ingested from payment gateway, bank statement,
or merchant order system.
No business logic — pure data definition only.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import TransactionSource, TransactionStatus

if TYPE_CHECKING:
    from app.models.merchant import Merchant
    from app.models.reconciliation_result import ReconciliationResult


class Transaction(Base):
    """
    Core financial transaction record.

    Money columns use Numeric(18, 4) — never Float — to preserve
    decimal precision for financial calculations.
    """

    __tablename__ = "transactions"

    # ------------------------------------------------------------------
    # Composite indexes defined at table level
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_transactions_transaction_reference", "transaction_reference"),
        Index("ix_transactions_order_reference", "order_reference"),
        Index("ix_transactions_transaction_date", "transaction_date"),
        Index("ix_transactions_merchant_id", "merchant_id"),
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
    transaction_reference: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    order_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
        nullable=True,
    )
    customer_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ------------------------------------------------------------------
    # Financial data  (Numeric — never Float)
    # ------------------------------------------------------------------
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD", server_default="USD"
    )

    # ------------------------------------------------------------------
    # Transaction metadata
    # ------------------------------------------------------------------
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    gateway: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ------------------------------------------------------------------
    # Status / source enums
    # ------------------------------------------------------------------
    status: Mapped[Optional[TransactionStatus]] = mapped_column(
        Enum(TransactionStatus, name="transactionstatus", create_type=True),
        nullable=True,
    )
    source: Mapped[Optional[TransactionSource]] = mapped_column(
        Enum(TransactionSource, name="transactionsource", create_type=True),
        nullable=True,
    )

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
    merchant: Mapped[Optional["Merchant"]] = relationship(
        "Merchant",
        back_populates="transactions",
        lazy="select",
    )
    reconciliation_results: Mapped[List["ReconciliationResult"]] = relationship(
        "ReconciliationResult",
        back_populates="transaction",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Transaction ref={self.transaction_reference!r} "
            f"amount={self.amount} {self.currency} status={self.status}>"
        )
