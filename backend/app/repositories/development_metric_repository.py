"""Development metric persistence."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.development_metric import DevelopmentMetric


class DevelopmentMetricRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        project_id: UUID,
        created_by: UUID,
        metrics_focus: str,
        context_text: str | None,
        status: str = "pending",
    ) -> DevelopmentMetric:
        row = DevelopmentMetric(
            project_id=project_id,
            created_by=created_by,
            metrics_focus=metrics_focus,
            context_text=context_text,
            status=status,
        )
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def update(self, row: DevelopmentMetric) -> DevelopmentMetric:
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def get_by_id_for_project(
        self,
        metric_id: UUID,
        project_id: UUID,
    ) -> DevelopmentMetric | None:
        stmt = select(DevelopmentMetric).where(
            DevelopmentMetric.id == metric_id,
            DevelopmentMetric.project_id == project_id,
        )
        return self._db.scalar(stmt)

    def list_by_project(
        self,
        project_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[DevelopmentMetric], int]:
        count_stmt = (
            select(func.count())
            .select_from(DevelopmentMetric)
            .where(DevelopmentMetric.project_id == project_id)
        )
        total = int(self._db.scalar(count_stmt) or 0)
        stmt = (
            select(DevelopmentMetric)
            .where(DevelopmentMetric.project_id == project_id)
            .order_by(DevelopmentMetric.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(stmt).all()), total
