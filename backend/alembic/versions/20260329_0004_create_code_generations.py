"""Create code_generations table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260329_0004"
down_revision: str | None = "20260328_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "code_generations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("technical_plan_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("task_description", sa.Text(), nullable=False),
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
            ["technical_plan_id"],
            ["technical_plans.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_code_generations_project_id"),
        "code_generations",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_code_generations_technical_plan_id"),
        "code_generations",
        ["technical_plan_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_code_generations_created_by"),
        "code_generations",
        ["created_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_code_generations_created_by"), table_name="code_generations")
    op.drop_index(
        op.f("ix_code_generations_technical_plan_id"),
        table_name="code_generations",
    )
    op.drop_index(op.f("ix_code_generations_project_id"), table_name="code_generations")
    op.drop_table("code_generations")
