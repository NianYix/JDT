"""Synchronous SQLAlchemy engine and session factory.

Uses sync drivers intentionally. Engine is built lazily from Settings so tests
can override DATABASE_URL before first use.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def _create_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        # :memory: needs StaticPool so schema is shared across connections.
        if ":memory:" in database_url:
            return create_engine(
                database_url,
                connect_args=connect_args,
                poolclass=StaticPool,
            )
        return create_engine(database_url, connect_args=connect_args)
    return create_engine(database_url, pool_pre_ping=True)


def get_engine() -> Engine:
    global _engine, SessionLocal
    if _engine is None:
        _engine = _create_engine(get_settings().database_url)
        SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def reset_engine() -> None:
    """Drop cached engine (used by tests after Settings override)."""
    global _engine, SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session for FastAPI Depends."""
    get_engine()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
