"""Limits and denylists for read-only repository browsing."""

from __future__ import annotations

from typing import Final

MAX_TREE_DEPTH: Final = 6
MAX_TREE_ENTRIES: Final = 500
MAX_FILE_BYTES: Final = 256 * 1024
MAX_SELECTED_FILES: Final = 20
MAX_SELECTED_TOTAL_BYTES: Final = 512 * 1024

IGNORED_DIR_NAMES: Final = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "dist",
        "build",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        ".idea",
        ".vscode",
        "coverage",
        ".next",
        "target",
    }
)

BINARY_EXTENSIONS: Final = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".bmp",
        ".pdf",
        ".zip",
        ".gz",
        ".tar",
        ".7z",
        ".rar",
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".mp3",
        ".mp4",
        ".avi",
        ".mov",
        ".class",
        ".pyc",
        ".pyo",
        ".o",
        ".a",
        ".wasm",
        ".sqlite",
        ".db",
    }
)
