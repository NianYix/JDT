"""Technical plan persistence."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.technical_plan import TechnicalPlan


class TechnicalPlanRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        project_id: UUID,
        created_by: UUID,
        requirement_analysis_id: UUID | None,
        context_text: str | None,
        selected_files_json: list[str] | None = None,
        status: str = "pending",
    ) -> TechnicalPlan:
        row = TechnicalPlan(
            project_id=project_id,
            created_by=created_by,
            requirement_analysis_id=requirement_analysis_id,
            context_text=context_text,
            selected_files_json=selected_files_json,
            status=status,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def update(self, row: TechnicalPlan) -> TechnicalPlan:
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def get_by_id_for_project(
        self,
        plan_id: UUID,
        project_id: UUID,
    ) -> TechnicalPlan | None:
        stmt = select(TechnicalPlan).where(
            TechnicalPlan.id == plan_id,
            TechnicalPlan.project_id == project_id,
        )
        return self._db.scalar(stmt)

    def list_by_project(
        self,
        project_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[TechnicalPlan], int]:
        count_stmt = (
            select(func.count())
            .select_from(TechnicalPlan)
            .where(TechnicalPlan.project_id == project_id)
        )
        total = int(self._db.scalar(count_stmt) or 0)
        stmt = (
            select(TechnicalPlan)
            .where(TechnicalPlan.project_id == project_id)
            .order_by(TechnicalPlan.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(stmt).all()), total
