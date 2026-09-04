"""Development metrics use cases (async AI job)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.user import User
from app.repositories.code_generation_repository import CodeGenerationRepository
from app.repositories.code_review_repository import CodeReviewRepository
from app.repositories.debug_session_repository import DebugSessionRepository
from app.repositories.development_metric_repository import DevelopmentMetricRepository
from app.repositories.requirement_analysis_repository import RequirementAnalysisRepository
from app.repositories.technical_plan_repository import TechnicalPlanRepository
from app.repositories.test_generation_repository import TestGenerationRepository
from app.schemas.common import PageResponse
from app.schemas.development_metric import (
    DevelopmentMetricCreate,
    DevelopmentMetricPublic,
)
from app.services.ai_job import (
    AiJobStatus,
    require_owned_project,
    safe_error_message,
    schedule_ai_job,
    with_worker_session,
)
from app.services.llm import factory as llm_factory
from app.services.llm.base import LLMProvider

logger = logging.getLogger(__name__)

_MAX_RECENT_SUMMARIES = 3


class DevelopmentMetricService:
    def __init__(
        self,
        db: Session,
        *,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self._db = db
        self._metrics = DevelopmentMetricRepository(db)
        self._llm_provider = llm_provider

    @staticmethod
    def _stage_line(stage_key: str, items: list[Any]) -> str:
        total = len(items)
        succeeded = sum(1 for item in items if item.status == AiJobStatus.SUCCEEDED)
        failed = sum(1 for item in items if item.status == AiJobStatus.FAILED)
        summaries: list[str] = []
        for item in items:
            if item.status != AiJobStatus.SUCCEEDED:
                continue
            summary = None
            if item.result_json and isinstance(item.result_json, dict):
                summary = item.result_json.get("summary")
            if summary and str(summary).strip():
                summaries.append(str(summary).strip())
            if len(summaries) >= _MAX_RECENT_SUMMARIES:
                break
        summaries_repr = summaries if summaries else ["(none)"]
        return (
            f"{stage_key}: total={total}, succeeded={succeeded}, failed={failed}, "
            f"recent_summaries={summaries_repr}"
        )

    @staticmethod
    def _build_workflow_summary(db: Session, project_id: UUID) -> str:
        page_size = 100
        lines: list[str] = ["--- Workflow Statistics ---"]

        analyses = RequirementAnalysisRepository(db)
        plans = TechnicalPlanRepository(db)
        code_gens = CodeGenerationRepository(db)
        test_gens = TestGenerationRepository(db)
        reviews = CodeReviewRepository(db)
        debug_sessions = DebugSessionRepository(db)
        metrics = DevelopmentMetricRepository(db)

        ra_items, _ = analyses.list_by_project(project_id, page=1, page_size=page_size)
        lines.append(DevelopmentMetricService._stage_line("requirement_analysis", ra_items))

        tp_items, _ = plans.list_by_project(project_id, page=1, page_size=page_size)
        lines.append(DevelopmentMetricService._stage_line("technical_planning", tp_items))

        cg_items, _ = code_gens.list_by_project(project_id, page=1, page_size=page_size)
        lines.append(DevelopmentMetricService._stage_line("ai_coding", cg_items))

        tg_items, _ = test_gens.list_by_project(project_id, page=1, page_size=page_size)
        lines.append(DevelopmentMetricService._stage_line("automated_testing", tg_items))

        cr_items, _ = reviews.list_by_project(project_id, page=1, page_size=page_size)
        lines.append(DevelopmentMetricService._stage_line("code_review", cr_items))

        db_items, _ = debug_sessions.list_by_project(project_id, page=1, page_size=page_size)
        lines.append(DevelopmentMetricService._stage_line("ai_debugging", db_items))

        dm_items, _ = metrics.list_by_project(project_id, page=1, page_size=page_size)
        lines.append(DevelopmentMetricService._stage_line("development_metrics", dm_items))

        return "\n".join(lines)

    @staticmethod
    def _build_context(
        db: Session,
        project_id: UUID,
        *,
        metrics_focus: str,
        context_text: str | None,
    ) -> str:
        sections = [
            f"--- Metrics Focus ---\n{metrics_focus}",
            DevelopmentMetricService._build_workflow_summary(db, project_id),
        ]
        if context_text:
            sections.append("--- Additional Context ---\n" + context_text)
        return "\n\n".join(sections)

    def create(
        self,
        owner: User,
        project_id: UUID,
        payload: DevelopmentMetricCreate,
        background_tasks: BackgroundTasks,
    ) -> DevelopmentMetricPublic:
        require_owned_project(self._db, owner, project_id)
        context_text = (payload.context_text or "").strip() or None

        row = self._metrics.create(
            project_id=project_id,
            created_by=owner.id,
            metrics_focus=payload.metrics_focus,
            context_text=context_text,
            status=AiJobStatus.PENDING,
        )

        provider = self._llm_provider
        record_id = row.id

        def _job() -> None:
            DevelopmentMetricService._execute(record_id, project_id, provider)

        schedule_ai_job(background_tasks, _job)
        return DevelopmentMetricPublic.model_validate(row)

    @staticmethod
    def _execute(
        record_id: UUID,
        project_id: UUID,
        llm_provider: LLMProvider | None,
    ) -> None:
        def _run(db: Session) -> None:
            repo = DevelopmentMetricRepository(db)
            row = repo.get_by_id_for_project(record_id, project_id)
            if row is None or row.status not in {AiJobStatus.PENDING, AiJobStatus.RUNNING}:
                return
            row.status = AiJobStatus.RUNNING
            repo.update(row)
            model_name = None
            try:
                provider = llm_provider or llm_factory.get_llm_provider()
                model_name = provider.model_name
                llm_context = DevelopmentMetricService._build_context(
                    db,
                    project_id,
                    metrics_focus=row.metrics_focus,
                    context_text=row.context_text,
                )
                result = provider.generate_metrics(llm_context)
                row.status = AiJobStatus.SUCCEEDED
                row.result_json = result.model_dump()
                row.model_name = model_name
                row.error_message = None
            except Exception as exc:  # noqa: BLE001
                logger.exception("Development metrics LLM failed: %s", exc)
                row.status = AiJobStatus.FAILED
                row.result_json = None
                row.model_name = model_name
                row.error_message = safe_error_message(exc)
            repo.update(row)

        with_worker_session(_run)

    def list_for_project(
        self,
        owner: User,
        project_id: UUID,
        *,
        page: int,
        page_size: int,
    ) -> PageResponse[DevelopmentMetricPublic]:
        require_owned_project(self._db, owner, project_id)
        items, total = self._metrics.list_by_project(
            project_id,
            page=page,
            page_size=page_size,
        )
        return PageResponse(
            items=[DevelopmentMetricPublic.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_for_project(
        self,
        owner: User,
        project_id: UUID,
        metric_id: UUID,
    ) -> DevelopmentMetricPublic:
        require_owned_project(self._db, owner, project_id)
        row = self._metrics.get_by_id_for_project(metric_id, project_id)
        if row is None:
            raise AppError(
                "Development metric not found",
                code="development_metric_not_found",
                status_code=404,
            )
        return DevelopmentMetricPublic.model_validate(row)
