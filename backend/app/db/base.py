"""SQLAlchemy declarative base (no business tables in this phase)."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Metadata root for future models; intentionally empty for foundation stage."""
