"""Test generation persistence."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.test_generation import TestGeneration


class TestGenerationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        project_id: UUID,
        created_by: UUID,
        code_generation_id: UUID | None,
        target_description: str,
        context_text: str | None,
        selected_files_json: list[str] | None = None,
        status: str = "pending",
    ) -> TestGeneration:
        row = TestGeneration(
            project_id=project_id,
            created_by=created_by,
            code_generation_id=code_generation_id,
            target_description=target_description,
            context_text=context_text,
            selected_files_json=selected_files_json,
            status=status,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def update(self, row: TestGeneration) -> TestGeneration:
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def get_by_id_for_project(
        self,
        generation_id: UUID,
        project_id: UUID,
    ) -> TestGeneration | None:
        stmt = select(TestGeneration).where(
            TestGeneration.id == generation_id,
            TestGeneration.project_id == project_id,
        )
        return self._db.scalar(stmt)

    def list_by_project(
        self,
        project_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[TestGeneration], int]:
        count_stmt = (
            select(func.count())
            .select_from(TestGeneration)
            .where(TestGeneration.project_id == project_id)
        )
        total = int(self._db.scalar(count_stmt) or 0)
        stmt = (
            select(TestGeneration)
            .where(TestGeneration.project_id == project_id)
            .order_by(TestGeneration.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(stmt).all()), total
