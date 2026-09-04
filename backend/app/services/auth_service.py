"""Authentication use cases."""

from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.user import UserPublic, UserLoginRequest, UserRegisterRequest


class AuthService:
    def __init__(self, db: Session) -> None:
        self._users = UserRepository(db)

    def register(self, payload: UserRegisterRequest) -> UserPublic:
        if self._users.get_by_email(payload.email) is not None:
            raise AppError(
                "Email already registered",
                code="email_already_registered",
                status_code=409,
            )
        user = self._users.create(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            display_name=payload.display_name,
        )
        return UserPublic.model_validate(user)

    def login(self, payload: UserLoginRequest) -> TokenResponse:
        user = self._users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise AppError(
                "Invalid email or password",
                code="invalid_credentials",
                status_code=401,
            )
        token = create_access_token(subject=user.id, email=user.email)
        return TokenResponse(
            access_token=token,
            user=UserPublic.model_validate(user),
        )
