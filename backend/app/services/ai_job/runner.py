"""In-process AI job scheduling (no Redis / Celery).

Background tasks run after the HTTP response is sent. Each worker opens its own
DB session. Crashed mid-flight `running` rows are not auto-recovered in Phase 11.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_engine
from app.db import session as db_session

logger = logging.getLogger(__name__)

T = TypeVar("T")


def with_worker_session(fn: Callable[[Session], T]) -> T:
    """Open a fresh SessionLocal, run fn, always close."""
    get_engine()
    assert db_session.SessionLocal is not None
    db = db_session.SessionLocal()
    try:
        return fn(db)
    finally:
        db.close()


def schedule_ai_job(
    background_tasks: BackgroundTasks,
    fn: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> None:
    """Queue a sync worker function on FastAPI BackgroundTasks."""

    def _wrapper() -> None:
        try:
            fn(*args, **kwargs)
        except Exception:  # noqa: BLE001 — last-resort log; workers should self-handle
            logger.exception("AI background job crashed without handling")

    background_tasks.add_task(_wrapper)
