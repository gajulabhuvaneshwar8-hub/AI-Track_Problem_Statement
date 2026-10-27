"""
Add import_batches table.

Creates the import_batches table to track CSV/Excel file ingestion runs,
along with importstatus and importsource enum types.

Revision: 0002_add_import_batches
Revises: 0001_initial_schema
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = "0002_add_import_batches"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Enum types
    # ------------------------------------------------------------------
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        importsource = postgresql.ENUM(
            "gateway", "bank", "settlement",
            name="importsource",
            create_type=False,
        )
        importsource.create(bind, checkfirst=True)

        importstatus = postgresql.ENUM(
            "processing", "completed", "completed_with_errors", "failed",
            name="importstatus",
            create_type=False,
        )
        importstatus.create(bind, checkfirst=True)

    # ------------------------------------------------------------------
    # import_batches table
    # ------------------------------------------------------------------
    op.create_table(
        "import_batches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "merchant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("merchants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(20), nullable=False),
        sa.Column(
            "source",
            postgresql.ENUM("gateway", "bank", "settlement", name="importsource", create_type=False),
            nullable=False,
        ),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("invalid_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "status",
            postgresql.ENUM("processing", "completed", "completed_with_errors", "failed", name="importstatus", create_type=False),
            nullable=False,
            server_default="processing",
        ),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_import_batches_merchant_id", "import_batches", ["merchant_id"])
    op.create_index("ix_import_batches_created_at", "import_batches", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_import_batches_created_at", table_name="import_batches")
    op.drop_index("ix_import_batches_merchant_id", table_name="import_batches")
    op.drop_table("import_batches")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS importstatus")
        op.execute("DROP TYPE IF EXISTS importsource")
