"""
Add agent_investigations table.

Creates the agent_investigations table to store AI Reconciliation Investigation Agent
records, findings, decisions, evidence, and escalation recommendations.

Revision: 0004_add_agent_investigations
Revises: 0003_add_ai_analyses
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = "0004_add_agent_investigations"
down_revision: str | None = "0003_add_ai_analyses"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        investigationstatus = postgresql.ENUM(
            "pending",
            "investigating",
            "completed",
            "failed",
            name="investigationstatus",
            create_type=False,
        )
        investigationstatus.create(bind, checkfirst=True)

        agentdecision = postgresql.ENUM(
            "monitor",
            "review",
            "escalate",
            name="agentdecision",
            create_type=False,
        )
        agentdecision.create(bind, checkfirst=True)

    op.create_table(
        "agent_investigations",
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
            "status",
            postgresql.ENUM(
                "pending",
                "investigating",
                "completed",
                "failed",
                name="investigationstatus",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "investigation_type",
            sa.String(100),
            nullable=False,
            server_default="general_investigation",
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "confirmed_facts",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "possible_causes",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column(
            "impact",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column(
            "decision",
            postgresql.ENUM("monitor", "review", "escalate", name="agentdecision", create_type=False),
            nullable=False,
            server_default="review",
        ),
        sa.Column(
            "risk_level",
            postgresql.ENUM("low", "medium", "high", "critical", name="risklevel", create_type=False),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("confidence_score", sa.Numeric(5, 4), nullable=True),
        sa.Column(
            "escalation_required",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("escalation_team", sa.String(100), nullable=True),
        sa.Column(
            "evidence",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_agent_inv_reconciliation_id",
        "agent_investigations",
        ["reconciliation_id"],
    )
    op.create_index(
        "ix_agent_inv_exception_id",
        "agent_investigations",
        ["exception_id"],
    )
    op.create_index(
        "ix_agent_inv_status",
        "agent_investigations",
        ["status"],
    )
    op.create_index(
        "ix_agent_inv_decision",
        "agent_investigations",
        ["decision"],
    )
    op.create_index(
        "ix_agent_inv_risk_level",
        "agent_investigations",
        ["risk_level"],
    )
    op.create_index(
        "ix_agent_inv_created_at",
        "agent_investigations",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_inv_created_at", table_name="agent_investigations")
    op.drop_index("ix_agent_inv_risk_level", table_name="agent_investigations")
    op.drop_index("ix_agent_inv_decision", table_name="agent_investigations")
    op.drop_index("ix_agent_inv_status", table_name="agent_investigations")
    op.drop_index("ix_agent_inv_exception_id", table_name="agent_investigations")
    op.drop_index("ix_agent_inv_reconciliation_id", table_name="agent_investigations")
    op.drop_table("agent_investigations")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS agentdecision")
        op.execute("DROP TYPE IF EXISTS investigationstatus")
