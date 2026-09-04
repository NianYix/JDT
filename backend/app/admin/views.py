"""SQLAdmin model views for database CRUD."""

from __future__ import annotations

import uuid
from typing import Any

from sqladmin import ModelView
from sqlalchemy import select
from starlette.requests import Request
from wtforms import Form, PasswordField, SelectField, validators

from app.core.security import hash_password
from app.models.project import Project
from app.models.user import User


class UserAdmin(ModelView, model=User):
    """Manage users; password is write-only via a scaffolded form field."""

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    column_list = [User.id, User.email, User.display_name, User.created_at, User.updated_at]
    column_searchable_list = [User.email, User.display_name]
    column_sortable_list = [User.email, User.created_at]
    column_details_exclude_list = [User.hashed_password]
    form_excluded_columns = [User.hashed_password, User.projects, User.created_at, User.updated_at]
    form_include_pk = False

    async def scaffold_form(self, rules: list[str] | None = None) -> type[Form]:
        base_form = await super().scaffold_form(rules)

        class UserForm(base_form):  # type: ignore[misc,valid-type]
            password = PasswordField(
                "Password",
                validators=[
                    validators.Optional(),
                    validators.Length(min=8, max=128),
                ],
                description="创建时必填；编辑时留空表示不修改密码",
            )

        UserForm.__name__ = f"{base_form.__name__}WithPassword"
        return UserForm

    async def on_model_change(
        self,
        data: dict[str, Any],
        model: Any,
        is_created: bool,
        request: Request,
    ) -> None:
        password = data.pop("password", None)
        if isinstance(password, str):
            password = password.strip() or None

        if is_created:
            data.setdefault("id", uuid.uuid4())
            if not password:
                raise ValueError("创建用户时必须填写 Password（至少 8 位）")
            data["hashed_password"] = hash_password(password)
        elif password:
            data["hashed_password"] = hash_password(password)

        await super().on_model_change(data, model, is_created, request)


class ProjectAdmin(ModelView, model=Project):
    """Manage projects with an Owner dropdown labeled by display_name."""

    name = "Project"
    name_plural = "Projects"
    icon = "fa-solid fa-folder"

    column_list = [
        Project.id,
        Project.name,
        Project.owner_id,
        Project.repo_path,
        Project.created_at,
        Project.updated_at,
    ]
    column_searchable_list = [Project.name, Project.repo_path]
    column_sortable_list = [Project.name, Project.created_at]
    # Hide relationship + timestamps; owner is injected as SelectField in scaffold_form.
    form_excluded_columns = [
        Project.created_at,
        Project.updated_at,
        Project.owner,
        Project.owner_id,
    ]
    form_include_pk = False

    def _owner_choices(self) -> list[tuple[str, str]]:
        with self.session_maker() as session:
            rows = session.execute(
                select(User.id, User.display_name, User.email).order_by(User.display_name)
            ).all()
        return [
            (str(user_id), display_name or email or str(user_id))
            for user_id, display_name, email in rows
        ]

    async def scaffold_form(self, rules: list[str] | None = None) -> type[Form]:
        base_form = await super().scaffold_form(rules)
        choices = self._owner_choices()

        class ProjectForm(base_form):  # type: ignore[misc,valid-type]
            owner_id = SelectField(
                "Owner",
                choices=choices,
                validators=[validators.DataRequired(message="请选择 Owner")],
                description="下拉显示用户 display_name",
            )

        ProjectForm.__name__ = f"{base_form.__name__}WithOwner"
        return ProjectForm

    async def on_model_change(
        self,
        data: dict[str, Any],
        model: Any,
        is_created: bool,
        request: Request,
    ) -> None:
        if is_created:
            data.setdefault("id", uuid.uuid4())

        for key in ("description", "repo_path"):
            if key in data and data[key] == "":
                data[key] = None

        owner_raw = data.get("owner_id")
        if owner_raw is None or owner_raw == "" or owner_raw == "__None":
            raise ValueError("创建/保存项目时必须选择 Owner（所属用户）")

        try:
            data["owner_id"] = uuid.UUID(str(owner_raw))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"无效的 Owner: {owner_raw!r}") from exc

        # Drop non-column keys that may sneak in from the form.
        data.pop("owner", None)
        data.pop("password", None)

        await super().on_model_change(data, model, is_created, request)
