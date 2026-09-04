"""Code generation use cases (async AI job)."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.user import User
from app.repositories.code_generation_repository import CodeGenerationRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.technical_plan_repository import TechnicalPlanRepository
from app.schemas.code_generation import CodeGenerationCreate, CodeGenerationPublic
from app.schemas.common import PageResponse
from app.services import repo_service
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


class CodeGenerationService:
    def __init__(
        self,
        db: Session,
        *,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self._db = db
        self._plans = TechnicalPlanRepository(db)
        self._generations = CodeGenerationRepository(db)
        self._llm_provider = llm_provider

    @staticmethod
    def _build_context(
        db: Session,
        project_id: UUID,
        *,
        task_description: str,
        technical_plan_id: UUID | None,
        context_text: str | None,
        selected_files: list[str],
    ) -> str:
        sections: list[str] = [f"--- Coding Task ---\n{task_description}"]
        plans = TechnicalPlanRepository(db)

        if technical_plan_id is not None:
            plan = plans.get_by_id_for_project(technical_plan_id, project_id)
            if plan is None or plan.status != AiJobStatus.SUCCEEDED:
                raise AppError(
                    "Technical plan is missing or not succeeded",
                    code="invalid_technical_plan",
                    status_code=400,
                )
            if plan.result_json:
                sections.append(
                    "--- Technical Plan (JSON) ---\n"
                    + json.dumps(plan.result_json, ensure_ascii=False, indent=2)
                )
            elif plan.context_text:
                sections.append("--- Technical Plan (context) ---\n" + plan.context_text)

        if context_text:
            sections.append("--- Additional Context ---\n" + context_text)

        if selected_files:
            project = ProjectRepository(db).get_by_id(project_id)
            if project is None:
                raise AppError("Project not found", code="project_not_found", status_code=404)
            sections.append(repo_service.load_selected_files_for_prompt(project, selected_files))

        return "\n\n".join(sections)

    def create(
        self,
        owner: User,
        project_id: UUID,
        payload: CodeGenerationCreate,
        background_tasks: BackgroundTasks,
    ) -> CodeGenerationPublic:
        project = require_owned_project(self._db, owner, project_id)
        selected = list(payload.selected_files or [])
        if selected:
            selected = repo_service.validate_selected_paths(project, selected)

        plan_id = payload.technical_plan_id
        context_text = (payload.context_text or "").strip() or None
        if plan_id is not None:
            plan = self._plans.get_by_id_for_project(plan_id, project_id)
            if plan is None or plan.status != AiJobStatus.SUCCEEDED:
                raise AppError(
                    "Technical plan is missing or not succeeded",
                    code="invalid_technical_plan",
                    status_code=400,
                )

        row = self._generations.create(
            project_id=project_id,
            created_by=owner.id,
            technical_plan_id=plan_id,
            task_description=payload.task_description,
            context_text=context_text,
            selected_files_json=selected or None,
            status=AiJobStatus.PENDING,
        )

        provider = self._llm_provider
        record_id = row.id

        def _job() -> None:
            CodeGenerationService._execute(record_id, project_id, provider)

        schedule_ai_job(background_tasks, _job)
        return CodeGenerationPublic.model_validate(row)

    @staticmethod
    def _execute(
        record_id: UUID,
        project_id: UUID,
        llm_provider: LLMProvider | None,
    ) -> None:
        def _run(db: Session) -> None:
            repo = CodeGenerationRepository(db)
            row = repo.get_by_id_for_project(record_id, project_id)
            if row is None or row.status not in {AiJobStatus.PENDING, AiJobStatus.RUNNING}:
                return
            row.status = AiJobStatus.RUNNING
            repo.update(row)

            model_name = None
            try:
                provider = llm_provider or llm_factory.get_llm_provider()
                model_name = provider.model_name
                llm_context = CodeGenerationService._build_context(
                    db,
                    project_id,
                    task_description=row.task_description,
                    technical_plan_id=row.technical_plan_id,
                    context_text=row.context_text,
                    selected_files=row.selected_files,
                )
                result = provider.generate_code(llm_context)
                row.status = AiJobStatus.SUCCEEDED
                row.result_json = result.model_dump()
                row.model_name = model_name
                row.error_message = None
            except Exception as exc:  # noqa: BLE001
                logger.exception("Code generation LLM failed: %s", exc)
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
    ) -> PageResponse[CodeGenerationPublic]:
        require_owned_project(self._db, owner, project_id)
        items, total = self._generations.list_by_project(
            project_id,
            page=page,
            page_size=page_size,
        )
        return PageResponse(
            items=[CodeGenerationPublic.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_for_project(
        self,
        owner: User,
        project_id: UUID,
        generation_id: UUID,
    ) -> CodeGenerationPublic:
        require_owned_project(self._db, owner, project_id)
        row = self._generations.get_by_id_for_project(generation_id, project_id)
        if row is None:
            raise AppError(
                "Code generation not found",
                code="code_generation_not_found",
                status_code=404,
            )
        return CodeGenerationPublic.model_validate(row)
