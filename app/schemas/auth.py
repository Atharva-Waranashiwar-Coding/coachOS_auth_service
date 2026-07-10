"""Pydantic schemas for authentication workflows."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Request body for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.COACH


class UserLogin(BaseModel):
    """Request body for user login."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserRead(BaseModel):
    """Public user response model."""

    id: UUID
    email: EmailStr
    role: UserRole
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
