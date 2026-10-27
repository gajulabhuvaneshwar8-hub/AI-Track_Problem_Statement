"""
app/models/import_batch.py

ImportBatch ORM model.
Tracks metadata and outcome of file ingestion runs (CSV/Excel uploads).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.models.enums import ImportSource, ImportStatus

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class ImportBatch(Base):
    """Tracks a single file upload/import operation and its statistics."""

    __tablename__ = "import_batches"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[ImportSource] = mapped_column(
        Enum(ImportSource, name="importsource", create_type=True),
        nullable=False,
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[ImportStatus] = mapped_column(
        Enum(ImportStatus, name="importstatus", create_type=True),
        default=ImportStatus.processing,
        nullable=False,
    )
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    merchant: Mapped[Optional["Merchant"]] = relationship(
        "Merchant",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ImportBatch id={self.id} file={self.file_name!r} "
            f"source={self.source} status={self.status}>"
        )
