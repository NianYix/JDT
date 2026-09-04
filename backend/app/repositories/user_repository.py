"""User persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: UUID) -> User | None:
        return self._db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return self._db.scalar(stmt)

    def create(self, *, email: str, hashed_password: str, display_name: str) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            display_name=display_name,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
