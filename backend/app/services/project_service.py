"""Project use cases."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.common import PageResponse
from app.schemas.project import ProjectCreate, ProjectPublic, ProjectUpdate


class ProjectService:
    def __init__(self, db: Session) -> None:
        self._projects = ProjectRepository(db)

    def create(self, owner: User, payload: ProjectCreate) -> ProjectPublic:
        project = self._projects.create(
            owner_id=owner.id,
            name=payload.name,
            description=payload.description,
            repo_path=payload.repo_path,
        )
        return ProjectPublic.model_validate(project)

    def list_mine(
        self,
        owner: User,
        *,
        page: int,
        page_size: int,
    ) -> PageResponse[ProjectPublic]:
        items, total = self._projects.list_by_owner(owner.id, page=page, page_size=page_size)
        return PageResponse(
            items=[ProjectPublic.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_mine(self, owner: User, project_id: UUID) -> ProjectPublic:
        project = self._projects.get_by_id_for_owner(project_id, owner.id)
        if project is None:
            raise AppError("Project not found", code="project_not_found", status_code=404)
        return ProjectPublic.model_validate(project)

    def update_mine(
        self,
        owner: User,
        project_id: UUID,
        payload: ProjectUpdate,
    ) -> ProjectPublic:
        project = self._projects.get_by_id_for_owner(project_id, owner.id)
        if project is None:
            raise AppError("Project not found", code="project_not_found", status_code=404)

        data = payload.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(project, key, value)

        updated = self._projects.update(project)
        return ProjectPublic.model_validate(updated)

    def delete_mine(self, owner: User, project_id: UUID) -> None:
        project = self._projects.get_by_id_for_owner(project_id, owner.id)
        if project is None:
            raise AppError("Project not found", code="project_not_found", status_code=404)
        self._projects.delete(project)
