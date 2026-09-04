"""Create debug_sessions table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260401_0007"
down_revision: str | None = "20260331_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "debug_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("code_review_id", sa.Uuid(), nullable=True),
        sa.Column("code_generation_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("problem_description", sa.Text(), nullable=False),
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
            ["code_review_id"],
            ["code_reviews.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["code_generation_id"],
            ["code_generations.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_debug_sessions_project_id"),
        "debug_sessions",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_debug_sessions_code_review_id"),
        "debug_sessions",
        ["code_review_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_debug_sessions_code_generation_id"),
        "debug_sessions",
        ["code_generation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_debug_sessions_created_by"),
        "debug_sessions",
        ["created_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_debug_sessions_created_by"), table_name="debug_sessions")
    op.drop_index(
        op.f("ix_debug_sessions_code_generation_id"),
        table_name="debug_sessions",
    )
    op.drop_index(op.f("ix_debug_sessions_code_review_id"), table_name="debug_sessions")
    op.drop_index(op.f("ix_debug_sessions_project_id"), table_name="debug_sessions")
    op.drop_table("debug_sessions")
