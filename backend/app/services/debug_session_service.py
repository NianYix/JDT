"""Debug session use cases (async AI job)."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models.user import User
from app.repositories.code_generation_repository import CodeGenerationRepository
from app.repositories.code_review_repository import CodeReviewRepository
from app.repositories.debug_session_repository import DebugSessionRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.common import PageResponse
from app.schemas.debug_session import DebugSessionCreate, DebugSessionPublic
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


class DebugSessionService:
    def __init__(
        self,
        db: Session,
        *,
        llm_provider: LLMProvider | None = None,
    ) -> None:
        self._db = db
        self._reviews = CodeReviewRepository(db)
        self._code_generations = CodeGenerationRepository(db)
        self._sessions = DebugSessionRepository(db)
        self._llm_provider = llm_provider

    @staticmethod
    def _build_context(
        db: Session,
        project_id: UUID,
        *,
        problem_description: str,
        code_review_id: UUID | None,
        code_generation_id: UUID | None,
        context_text: str | None,
        selected_files: list[str],
    ) -> str:
        sections: list[str] = [f"--- Problem Description ---\n{problem_description}"]
        reviews = CodeReviewRepository(db)
        code_gens = CodeGenerationRepository(db)

        if code_review_id is not None:
            review = reviews.get_by_id_for_project(code_review_id, project_id)
            if review is None or review.status != AiJobStatus.SUCCEEDED:
                raise AppError(
                    "Code review is missing or not succeeded",
                    code="invalid_code_review",
                    status_code=400,
                )
            if review.result_json:
                sections.append(
                    "--- Code Review (JSON) ---\n"
                    + json.dumps(review.result_json, ensure_ascii=False, indent=2)
                )
            else:
                sections.append("--- Code Review (scope) ---\n" + review.review_scope)

        if code_generation_id is not None:
            code_gen = code_gens.get_by_id_for_project(code_generation_id, project_id)
            if code_gen is None or code_gen.status != AiJobStatus.SUCCEEDED:
                raise AppError(
                    "Code generation is missing or not succeeded",
                    code="invalid_code_generation",
                    status_code=400,
                )
            if code_gen.result_json:
                sections.append(
                    "--- Code Generation (JSON) ---\n"
                    + json.dumps(code_gen.result_json, ensure_ascii=False, indent=2)
                )
            else:
                sections.append(
                    "--- Code Generation (task) ---\n" + code_gen.task_description
                )

        if context_text:
            sections.append("--- Logs / Stack / Context ---\n" + context_text)

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
        payload: DebugSessionCreate,
        background_tasks: BackgroundTasks,
    ) -> DebugSessionPublic:
        project = require_owned_project(self._db, owner, project_id)
        selected = list(payload.selected_files or [])
        if selected:
            selected = repo_service.validate_selected_paths(project, selected)

        review_id = payload.code_review_id
        code_gen_id = payload.code_generation_id
        context_text = (payload.context_text or "").strip() or None

        if review_id is not None:
            review = self._reviews.get_by_id_for_project(review_id, project_id)
            if review is None or review.status != AiJobStatus.SUCCEEDED:
                raise AppError(
                    "Code review is missing or not succeeded",
                    code="invalid_code_review",
                    status_code=400,
                )

        if code_gen_id is not None:
            code_gen = self._code_generations.get_by_id_for_project(code_gen_id, project_id)
            if code_gen is None or code_gen.status != AiJobStatus.SUCCEEDED:
                raise AppError(
                    "Code generation is missing or not succeeded",
                    code="invalid_code_generation",
                    status_code=400,
                )

        row = self._sessions.create(
            project_id=project_id,
            created_by=owner.id,
            code_review_id=review_id,
            code_generation_id=code_gen_id,
            problem_description=payload.problem_description,
            context_text=context_text,
            selected_files_json=selected or None,
            status=AiJobStatus.PENDING,
        )

        provider = self._llm_provider
        record_id = row.id

        def _job() -> None:
            DebugSessionService._execute(record_id, project_id, provider)

        schedule_ai_job(background_tasks, _job)
        return DebugSessionPublic.model_validate(row)

    @staticmethod
    def _execute(
        record_id: UUID,
        project_id: UUID,
        llm_provider: LLMProvider | None,
    ) -> None:
        def _run(db: Session) -> None:
            repo = DebugSessionRepository(db)
            row = repo.get_by_id_for_project(record_id, project_id)
            if row is None or row.status not in {AiJobStatus.PENDING, AiJobStatus.RUNNING}:
                return
            row.status = AiJobStatus.RUNNING
            repo.update(row)
            model_name = None
            try:
                provider = llm_provider or llm_factory.get_llm_provider()
                model_name = provider.model_name
                llm_context = DebugSessionService._build_context(
                    db,
                    project_id,
                    problem_description=row.problem_description,
                    code_review_id=row.code_review_id,
                    code_generation_id=row.code_generation_id,
                    context_text=row.context_text,
                    selected_files=row.selected_files,
                )
                result = provider.debug_issue(llm_context)
                row.status = AiJobStatus.SUCCEEDED
                row.result_json = result.model_dump()
                row.model_name = model_name
                row.error_message = None
            except Exception as exc:  # noqa: BLE001
                logger.exception("Debug session LLM failed: %s", exc)
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
    ) -> PageResponse[DebugSessionPublic]:
        require_owned_project(self._db, owner, project_id)
        items, total = self._sessions.list_by_project(
            project_id,
            page=page,
            page_size=page_size,
        )
        return PageResponse(
            items=[DebugSessionPublic.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_for_project(
        self,
        owner: User,
        project_id: UUID,
        session_id: UUID,
    ) -> DebugSessionPublic:
        require_owned_project(self._db, owner, project_id)
        row = self._sessions.get_by_id_for_project(session_id, project_id)
        if row is None:
            raise AppError(
                "Debug session not found",
                code="debug_session_not_found",
                status_code=404,
            )
        return DebugSessionPublic.model_validate(row)
