"""Add selected_files_json to AI workflow tables that support repo context."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260403_0009"
down_revision: str | None = "20260402_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "technical_plans",
    "code_generations",
    "test_generations",
    "code_reviews",
    "debug_sessions",
)


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column("selected_files_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_column(table, "selected_files_json")
