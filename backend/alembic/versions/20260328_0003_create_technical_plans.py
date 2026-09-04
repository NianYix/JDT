"""Create technical_plans table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260328_0003"
down_revision: str | None = "20260327_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "technical_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("requirement_analysis_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("context_text", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=True),
        sa.Column("model_name", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["requirement_analysis_id"],
            ["requirement_analyses.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_technical_plans_project_id"),
        "technical_plans",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_technical_plans_requirement_analysis_id"),
        "technical_plans",
        ["requirement_analysis_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_technical_plans_created_by"),
        "technical_plans",
        ["created_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_technical_plans_created_by"), table_name="technical_plans")
    op.drop_index(
        op.f("ix_technical_plans_requirement_analysis_id"),
        table_name="technical_plans",
    )
    op.drop_index(op.f("ix_technical_plans_project_id"), table_name="technical_plans")
    op.drop_table("technical_plans")
