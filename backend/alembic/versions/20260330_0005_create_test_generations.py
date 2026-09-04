"""Create test_generations table."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260330_0005"
down_revision: str | None = "20260329_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "test_generations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("code_generation_id", sa.Uuid(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("target_description", sa.Text(), nullable=False),
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
            ["code_generation_id"],
            ["code_generations.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_test_generations_project_id"),
        "test_generations",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_test_generations_code_generation_id"),
        "test_generations",
        ["code_generation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_test_generations_created_by"),
        "test_generations",
        ["created_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_test_generations_created_by"), table_name="test_generations")
    op.drop_index(
        op.f("ix_test_generations_code_generation_id"),
        table_name="test_generations",
    )
    op.drop_index(op.f("ix_test_generations_project_id"), table_name="test_generations")
    op.drop_table("test_generations")
