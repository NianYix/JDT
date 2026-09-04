"""Code review persistence."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.code_review import CodeReview


class CodeReviewRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        project_id: UUID,
        created_by: UUID,
        code_generation_id: UUID | None,
        review_scope: str,
        context_text: str | None,
        selected_files_json: list[str] | None = None,
        status: str = "pending",
    ) -> CodeReview:
        row = CodeReview(
            project_id=project_id,
            created_by=created_by,
            code_generation_id=code_generation_id,
            review_scope=review_scope,
            context_text=context_text,
            selected_files_json=selected_files_json,
            status=status,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def update(self, row: CodeReview) -> CodeReview:
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def get_by_id_for_project(
        self,
        review_id: UUID,
        project_id: UUID,
    ) -> CodeReview | None:
        stmt = select(CodeReview).where(
            CodeReview.id == review_id,
            CodeReview.project_id == project_id,
        )
        return self._db.scalar(stmt)

    def list_by_project(
        self,
        project_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[CodeReview], int]:
        count_stmt = (
            select(func.count())
            .select_from(CodeReview)
            .where(CodeReview.project_id == project_id)
        )
        total = int(self._db.scalar(count_stmt) or 0)
        stmt = (
            select(CodeReview)
            .where(CodeReview.project_id == project_id)
            .order_by(CodeReview.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(stmt).all()), total
