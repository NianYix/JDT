"""Requirement analysis persistence."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.requirement_analysis import RequirementAnalysis


class RequirementAnalysisRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        project_id: UUID,
        created_by: UUID,
        source_text: str,
        status: str = "pending",
    ) -> RequirementAnalysis:
        row = RequirementAnalysis(
            project_id=project_id,
            created_by=created_by,
            source_text=source_text,
            status=status,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def update(self, row: RequirementAnalysis) -> RequirementAnalysis:
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def get_by_id_for_project(
        self,
        analysis_id: UUID,
        project_id: UUID,
    ) -> RequirementAnalysis | None:
        stmt = select(RequirementAnalysis).where(
            RequirementAnalysis.id == analysis_id,
            RequirementAnalysis.project_id == project_id,
        )
        return self._db.scalar(stmt)

    def list_by_project(
        self,
        project_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[RequirementAnalysis], int]:
        count_stmt = (
            select(func.count())
            .select_from(RequirementAnalysis)
            .where(RequirementAnalysis.project_id == project_id)
        )
        total = int(self._db.scalar(count_stmt) or 0)
        stmt = (
            select(RequirementAnalysis)
            .where(RequirementAnalysis.project_id == project_id)
            .order_by(RequirementAnalysis.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(stmt).all()), total
