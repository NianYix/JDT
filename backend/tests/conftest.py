"""Shared pytest fixtures — SQLite in-memory DB for Phase 2 tests."""

from __future__ import annotations

import os

# Must set before Settings / engine are first constructed.
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-pytest-only-32b"
os.environ["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["ADMIN_ENABLED"] = "true"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin123456"

import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db import session as db_session
from app.db.session import get_db, get_engine, reset_engine
from app.main import create_app
import app.models  # noqa: F401


@pytest.fixture()
def client() -> TestClient:
    reset_engine()
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

    def _override_get_db():
        assert db_session.SessionLocal is not None
        db = db_session.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    application = create_app()
    application.dependency_overrides[get_db] = _override_get_db

    with TestClient(application) as test_client:
        yield test_client

    application.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    reset_engine()
