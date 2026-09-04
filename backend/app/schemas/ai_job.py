"""Shared schema bits for AI workflows."""

from typing import Literal

from app.core.repo_limits import MAX_SELECTED_FILES

AiJobStatusLiteral = Literal["pending", "running", "succeeded", "failed"]


def normalize_selected_files_in_schema(value: list[str] | None) -> list[str]:
    if not value:
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in value:
        cleaned = (item or "").strip().replace("\\", "/")
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        out.append(cleaned)
    if len(out) > MAX_SELECTED_FILES:
        raise ValueError(f"At most {MAX_SELECTED_FILES} files can be selected")
    return out
