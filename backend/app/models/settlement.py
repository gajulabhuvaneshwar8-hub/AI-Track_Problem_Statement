"""
app/models/settlement.py

Settlement ORM model.
Represents a settlement batch from a payment processor to a merchant.
Contains gross amounts, fees, taxes, refunds, chargebacks, and net payout.
No business logic — pure data definition only.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import SettlementStatus

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class Settlement(Base):
    """
    Settlement batch record.

    All monetary columns use Numeric(18, 4) — never Float — so that fee
    and tax calculations remain exact.
    """

    __tablename__ = "settlements"

    # ------------------------------------------------------------------
    # Composite indexes defined at table level
    # ------------------------------------------------------------------
    __table_args__ = (
        Index("ix_settlements_settlement_reference", "settlement_reference"),
        Index("ix_settlements_settlement_date", "settlement_date"),
        Index("ix_settlements_merchant_id", "merchant_id"),
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
    settlement_reference: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Dates
    # ------------------------------------------------------------------
    settlement_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # ------------------------------------------------------------------
    # Financial data  (Numeric — never Float)
    # ------------------------------------------------------------------
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    fees: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0"), server_default="0"
    )
    taxes: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0"), server_default="0"
    )
    refunds: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0"), server_default="0"
    )
    chargebacks: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0"), server_default="0"
    )
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # ------------------------------------------------------------------
    # Status enum
    # ------------------------------------------------------------------
    status: Mapped[Optional[SettlementStatus]] = mapped_column(
        Enum(SettlementStatus, name="settlementstatus", create_type=True),
        nullable=True,
        default=SettlementStatus.pending,
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
        back_populates="settlements",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<Settlement ref={self.settlement_reference!r} "
            f"net={self.net_amount} status={self.status}>"
        )
