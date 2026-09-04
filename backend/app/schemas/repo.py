"""Repository browsing schemas."""

from pydantic import BaseModel, Field


class RepoTreeEntry(BaseModel):
    path: str
    name: str
    is_dir: bool
    size: int | None = None


class RepoTreeResponse(BaseModel):
    root: str
    entries: list[RepoTreeEntry] = Field(default_factory=list)


class RepoFileContent(BaseModel):
    path: str
    content: str
    size: int
    truncated: bool = False
