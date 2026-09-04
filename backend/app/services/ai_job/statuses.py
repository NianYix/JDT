"""AI job status constants and helpers."""

from __future__ import annotations

from typing import Final, Literal

AiJobStatusLiteral = Literal["pending", "running", "succeeded", "failed"]


class AiJobStatus:
    PENDING: Final = "pending"
    RUNNING: Final = "running"
    SUCCEEDED: Final = "succeeded"
    FAILED: Final = "failed"

    TERMINAL: Final = frozenset({SUCCEEDED, FAILED})


def safe_error_message(exc: BaseException, *, max_len: int = 2000) -> str:
    """Truncate exception text for client-facing persistence (no full traceback)."""
    text = str(exc).strip() or exc.__class__.__name__
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text
