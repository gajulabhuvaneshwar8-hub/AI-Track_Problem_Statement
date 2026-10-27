"""
app/models/merchant.py

Merchant ORM model.
Represents a business entity that processes payments through the platform.
No business logic — pure data definition only.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.settlement import Settlement
    from app.models.transaction import Transaction


class Merchant(Base):
    """A merchant / business entity registered on the platform."""

    __tablename__ = "merchants"

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
    # Identity
    # ------------------------------------------------------------------
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    business_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

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
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="merchant",
        lazy="select",
    )
    settlements: Mapped[List["Settlement"]] = relationship(
        "Settlement",
        back_populates="merchant",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Merchant id={self.id} business_name={self.business_name!r}>"
