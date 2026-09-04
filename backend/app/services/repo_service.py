"""Read-only repository tree and file access for a Project.repo_path."""

from __future__ import annotations

from pathlib import Path

from app.core.exceptions import AppError
from app.core.repo_limits import (
    BINARY_EXTENSIONS,
    IGNORED_DIR_NAMES,
    MAX_FILE_BYTES,
    MAX_SELECTED_FILES,
    MAX_SELECTED_TOTAL_BYTES,
    MAX_TREE_DEPTH,
    MAX_TREE_ENTRIES,
)
from app.models.project import Project
from app.schemas.repo import RepoFileContent, RepoTreeEntry, RepoTreeResponse


def _resolve_repo_root(project: Project) -> Path:
    raw = (project.repo_path or "").strip()
    if not raw:
        raise AppError(
            "Repository path is not configured",
            code="repo_not_configured",
            status_code=400,
        )
    root = Path(raw).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise AppError(
            "Repository path is unavailable",
            code="repo_unavailable",
            status_code=400,
        )
    return root


def _safe_join(root: Path, relative: str) -> Path:
    rel = (relative or "").strip().replace("\\", "/")
    if not rel or rel.startswith("/") or rel.startswith("~"):
        raise AppError(
            "Path is outside the repository",
            code="path_outside_repo",
            status_code=400,
        )
    if ".." in Path(rel).parts:
        raise AppError(
            "Path is outside the repository",
            code="path_outside_repo",
            status_code=400,
        )
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise AppError(
            "Path is outside the repository",
            code="path_outside_repo",
            status_code=400,
        ) from exc
    return target


def normalize_selected_files(paths: list[str] | None) -> list[str]:
    if not paths:
        return []
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in paths:
        cleaned = (raw or "").strip().replace("\\", "/")
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        ordered.append(cleaned)
    if len(ordered) > MAX_SELECTED_FILES:
        raise AppError(
            f"At most {MAX_SELECTED_FILES} files can be selected",
            code="too_many_selected_files",
            status_code=400,
        )
    return ordered


def validate_selected_paths(project: Project, paths: list[str]) -> list[str]:
    """Ensure selected relative paths exist as files under repo_path (no content read)."""
    normalized = normalize_selected_files(paths)
    if not normalized:
        return []
    root = _resolve_repo_root(project)
    for rel in normalized:
        target = _safe_join(root, rel)
        if not target.exists() or not target.is_file():
            raise AppError(
                f"Selected path is not a readable file: {rel}",
                code="path_not_file",
                status_code=400,
            )
        if target.suffix.lower() in BINARY_EXTENSIONS:
            raise AppError(
                f"Binary file not allowed: {rel}",
                code="binary_file_not_allowed",
                status_code=400,
            )
    return normalized


def list_tree(project: Project, *, max_depth: int | None = None) -> RepoTreeResponse:
    root = _resolve_repo_root(project)
    depth_cap = MAX_TREE_DEPTH if max_depth is None else min(max(1, max_depth), MAX_TREE_DEPTH)
    entries: list[RepoTreeEntry] = []

    def walk(current: Path, depth: int) -> None:
        if len(entries) >= MAX_TREE_ENTRIES or depth > depth_cap:
            return
        try:
            children = sorted(current.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return
        for child in children:
            if len(entries) >= MAX_TREE_ENTRIES:
                return
            name = child.name
            if name in IGNORED_DIR_NAMES:
                continue
            try:
                rel = child.relative_to(root).as_posix()
            except ValueError:
                continue
            is_dir = child.is_dir()
            size = None
            if not is_dir:
                try:
                    size = child.stat().st_size
                except OSError:
                    size = None
            entries.append(
                RepoTreeEntry(path=rel, name=name, is_dir=is_dir, size=size)
            )
            if is_dir and depth < depth_cap:
                walk(child, depth + 1)

    walk(root, 1)
    return RepoTreeResponse(root=str(root), entries=entries)


def read_file(project: Project, relative_path: str) -> RepoFileContent:
    root = _resolve_repo_root(project)
    target = _safe_join(root, relative_path)
    if not target.exists() or not target.is_file():
        raise AppError(
            "Path is not a readable file",
            code="path_not_file",
            status_code=400,
        )
    if target.suffix.lower() in BINARY_EXTENSIONS:
        raise AppError(
            "Binary file not allowed",
            code="binary_file_not_allowed",
            status_code=400,
        )
    try:
        size = target.stat().st_size
    except OSError as exc:
        raise AppError(
            "Failed to read file",
            code="file_read_failed",
            status_code=400,
        ) from exc
    if size > MAX_FILE_BYTES:
        raise AppError(
            f"File exceeds {MAX_FILE_BYTES} bytes",
            code="file_too_large",
            status_code=400,
        )
    try:
        raw = target.read_bytes()
    except OSError as exc:
        raise AppError(
            "Failed to read file",
            code="file_read_failed",
            status_code=400,
        ) from exc
    if b"\x00" in raw[:8192]:
        raise AppError(
            "Binary file not allowed",
            code="binary_file_not_allowed",
            status_code=400,
        )
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AppError(
            "Binary file not allowed",
            code="binary_file_not_allowed",
            status_code=400,
        ) from exc
    rel = target.relative_to(root).as_posix()
    return RepoFileContent(path=rel, content=content, size=len(raw), truncated=False)


def load_selected_files_for_prompt(project: Project, paths: list[str]) -> str:
    """Read selected files and format a prompt section. Any failure raises AppError."""
    normalized = normalize_selected_files(paths)
    if not normalized:
        return ""
    total = 0
    blocks: list[str] = ["--- Repository Files ---"]
    for rel in normalized:
        file_data = read_file(project, rel)
        total += file_data.size
        if total > MAX_SELECTED_TOTAL_BYTES:
            raise AppError(
                f"Selected files exceed {MAX_SELECTED_TOTAL_BYTES} bytes total",
                code="selected_files_too_large",
                status_code=400,
            )
        blocks.append(f"### {file_data.path}\n```\n{file_data.content}\n```")
    return "\n\n".join(blocks)
