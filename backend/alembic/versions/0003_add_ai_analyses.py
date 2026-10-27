"""
Add ai_analyses table.

Creates the ai_analyses table to store interpretive AI and fallback analyses
of reconciliation results and exceptions, along with analysistype, risklevel,
and analysisstatus enum types.

Revision: 0003_add_ai_analyses
Revises: 0002_add_import_batches
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = "0003_add_ai_analyses"
down_revision: str | None = "0002_add_import_batches"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        analysistype = postgresql.ENUM(
            "exception_analysis",
            "root_cause",
            "recommendation",
            "investigation",
            name="analysistype",
            create_type=False,
        )
        analysistype.create(bind, checkfirst=True)

        risklevel = postgresql.ENUM(
            "low",
            "medium",
            "high",
            "critical",
            name="risklevel",
            create_type=False,
        )
        risklevel.create(bind, checkfirst=True)

        analysisstatus = postgresql.ENUM(
            "completed",
            "fallback",
            "failed",
            name="analysisstatus",
            create_type=False,
        )
        analysisstatus.create(bind, checkfirst=True)

    op.create_table(
        "ai_analyses",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False
        ),
        sa.Column(
            "reconciliation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("reconciliation_results.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "exception_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("exceptions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "analysis_type",
            postgresql.ENUM(
                "exception_analysis",
                "root_cause",
                "recommendation",
                "investigation",
                name="analysistype",
                create_type=False,
            ),
            nullable=False,
            server_default="exception_analysis",
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("impact", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column(
            "risk_level",
            postgresql.ENUM("low", "medium", "high", "critical", name="risklevel", create_type=False),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("confidence_score", sa.Numeric(5, 4), nullable=True),
        sa.Column("ai_provider", sa.String(50), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM("completed", "fallback", "failed", name="analysisstatus", create_type=False),
            nullable=False,
            server_default="completed",
        ),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_ai_analyses_reconciliation_id", "ai_analyses", ["reconciliation_id"]
    )
    op.create_index("ix_ai_analyses_exception_id", "ai_analyses", ["exception_id"])
    op.create_index("ix_ai_analyses_analysis_type", "ai_analyses", ["analysis_type"])
    op.create_index("ix_ai_analyses_risk_level", "ai_analyses", ["risk_level"])
    op.create_index("ix_ai_analyses_status", "ai_analyses", ["status"])
    op.create_index("ix_ai_analyses_created_at", "ai_analyses", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_ai_analyses_created_at", table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_status", table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_risk_level", table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_analysis_type", table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_exception_id", table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_reconciliation_id", table_name="ai_analyses")
    op.drop_table("ai_analyses")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS analysisstatus")
        op.execute("DROP TYPE IF EXISTS risklevel")
        op.execute("DROP TYPE IF EXISTS analysistype")
