"""Project persistence."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        owner_id: UUID,
        name: str,
        description: str | None,
        repo_path: str | None,
    ) -> Project:
        project = Project(
            owner_id=owner_id,
            name=name,
            description=description,
            repo_path=repo_path,
        )
        self._db.add(project)
        self._db.commit()
        self._db.refresh(project)
        return project

    def get_by_id(self, project_id: UUID) -> Project | None:
        return self._db.scalar(select(Project).where(Project.id == project_id))

    def get_by_id_for_owner(self, project_id: UUID, owner_id: UUID) -> Project | None:
        stmt = select(Project).where(
            Project.id == project_id,
            Project.owner_id == owner_id,
        )
        return self._db.scalar(stmt)

    def list_by_owner(
        self,
        owner_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[Project], int]:
        count_stmt = select(func.count()).select_from(Project).where(Project.owner_id == owner_id)
        total = int(self._db.scalar(count_stmt) or 0)

        stmt = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = list(self._db.scalars(stmt).all())
        return items, total

    def update(self, project: Project) -> Project:
        self._db.add(project)
        self._db.commit()
        self._db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self._db.delete(project)
        self._db.commit()
