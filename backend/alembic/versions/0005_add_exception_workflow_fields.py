"""
Add workflow tracking fields to exceptions table.

Adds resolution_note, reviewer_note, resolved_by, ignored_by, ignored_at,
escalated_at, escalation_reason, updated_at, and merchant_id to exceptions table.

Revision: 0005_add_exception_workflow_fields
Revises: 0004_add_agent_investigations
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = "0005_add_exception_workflow_fields"
down_revision: str | None = "0004_add_agent_investigations"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.add_column(
        "exceptions",
        sa.Column(
            "resolved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "exceptions",
        sa.Column(
            "ignored_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "exceptions",
        sa.Column(
            "merchant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("merchants.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column("exceptions", sa.Column("resolution_note", sa.Text(), nullable=True))
    op.add_column("exceptions", sa.Column("reviewer_note", sa.Text(), nullable=True))
    op.add_column("exceptions", sa.Column("escalation_reason", sa.Text(), nullable=True))
    op.add_column("exceptions", sa.Column("ignored_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("exceptions", sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("exceptions", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_exceptions_merchant_id", "exceptions", ["merchant_id"])


def downgrade() -> None:
    op.drop_index("ix_exceptions_merchant_id", table_name="exceptions")
    op.drop_column("exceptions", "updated_at")
    op.drop_column("exceptions", "escalated_at")
    op.drop_column("exceptions", "ignored_at")
    op.drop_column("exceptions", "escalation_reason")
    op.drop_column("exceptions", "reviewer_note")
    op.drop_column("exceptions", "resolution_note")
    op.drop_column("exceptions", "merchant_id")
    op.drop_column("exceptions", "ignored_by")
    op.drop_column("exceptions", "resolved_by")
