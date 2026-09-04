"""Auth request/response schemas."""

from pydantic import BaseModel, Field

from app.schemas.user import UserPublic


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")
    user: UserPublic
