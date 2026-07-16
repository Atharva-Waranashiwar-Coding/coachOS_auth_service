"""Pydantic schemas for authentication workflows."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.user import UserRole, UserStatus


class UserCreate(BaseModel):
    """Request body for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    model_config = ConfigDict(extra="forbid")


class UserLogin(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    """Public user response model."""

    id: UUID
    email: EmailStr
    role: UserRole
    status: UserStatus
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Access token response model."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead


class TokenPayload(BaseModel):
    """Validated JWT payload."""

    user_id: UUID
    email: EmailStr
    role: UserRole


class InternalAthleteUserCreate(BaseModel):
    """Trusted Athlete Service request to create or reuse an athlete identity."""

    email: EmailStr
    athlete_id: UUID
    invited_by_user_id: UUID
    model_config = ConfigDict(extra="forbid")


class InternalAthleteUserResponse(BaseModel):
    auth_user_id: UUID
    user_status: UserStatus
    invitation_id: UUID | None
    development_invitation_url: str | None = None


class InvitationAcceptRequest(BaseModel):
    token: str = Field(min_length=32, max_length=512)
    password: str = Field(min_length=8, max_length=128)
    password_confirmation: str = Field(min_length=8, max_length=128)
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def passwords_match(self) -> "InvitationAcceptRequest":
        if self.password != self.password_confirmation:
            raise ValueError("password confirmation does not match")
        return self


class InvitationAcceptResponse(BaseModel):
    user: UserRead
    message: str = "Invitation accepted. You can now sign in."
