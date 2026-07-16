"""Authentication business logic."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateEmailError, InactiveUserError, InvalidCredentialsError
from app.core.security import password_service, token_service
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserRead

logger = logging.getLogger(__name__)


class AuthService:
    """Use cases for signup, login, and authenticated user lookup."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def signup(self, payload: UserCreate) -> User:
        """Register a user after validating email uniqueness."""
        normalized_email = payload.email.lower()

        if self.get_user_by_email(normalized_email):
            raise DuplicateEmailError()

        user = User(
            email=normalized_email,
            password_hash=password_service.hash_password(payload.password),
            role=UserRole.COACH,
            status=UserStatus.ACTIVE,
            is_active=True,
        )

        self.db.add(user)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise DuplicateEmailError() from exc

        self.db.refresh(user)
        logger.info("User registered", extra={"user_id": str(user.id), "role": user.role.value})
        return user

    def login(self, payload: UserLogin) -> TokenResponse:
        """Authenticate a user and return an access token."""
        user = self.get_user_by_email(payload.email.lower())
        if (
            not user
            or not user.password_hash
            or not password_service.verify_password(payload.password, user.password_hash)
        ):
            raise InvalidCredentialsError()

        if not user.is_active or user.status != UserStatus.ACTIVE:
            raise InactiveUserError()

        access_token = token_service.create_access_token(user)
        logger.info("User logged in", extra={"user_id": str(user.id), "role": user.role.value})
        return TokenResponse(access_token=access_token, user=UserRead.model_validate(user))

    def get_user_by_email(self, email: str) -> User | None:
        """Return a user by normalized email address."""
        statement = select(User).where(User.email == email.lower())
        return self.db.execute(statement).scalar_one_or_none()

    def get_user_by_id(self, user_id: UUID) -> User | None:
        """Return a user by ID."""
        statement = select(User).where(User.id == user_id)
        return self.db.execute(statement).scalar_one_or_none()
