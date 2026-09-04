"""FastAPI dependencies: DB session and current user."""

from collections.abc import Generator
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Resolve Bearer JWT to a persisted User or raise 401."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("Not authenticated", code="unauthorized", status_code=401)

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(str(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise AppError("Not authenticated", code="unauthorized", status_code=401) from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise AppError("Not authenticated", code="unauthorized", status_code=401)
    return user


# Re-export for callers that prefer importing deps only.
__all__ = ["get_current_user", "get_db", "Generator"]
