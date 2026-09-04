"""Create ORM tables for local SQLite fallback (when Docker/Postgres is unavailable).

Also adds missing selected_files_json columns on existing SQLite DBs.
"""

from sqlalchemy import inspect, text

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_engine, reset_engine
import app.models  # noqa: F401

_SELECTED_FILES_TABLES = (
    "technical_plans",
    "code_generations",
    "test_generations",
    "code_reviews",
    "debug_sessions",
)


def _ensure_selected_files_columns(engine) -> None:
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in _SELECTED_FILES_TABLES:
            if table not in inspector.get_table_names():
                continue
            cols = {c["name"] for c in inspector.get_columns(table)}
            if "selected_files_json" not in cols:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN selected_files_json JSON"))


def main() -> None:
    reset_engine()
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        _ensure_selected_files_columns(engine)
    print(f"[OK] Tables ready on {get_settings().database_url}")


if __name__ == "__main__":
    main()
