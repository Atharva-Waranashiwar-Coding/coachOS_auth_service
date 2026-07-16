"""Password hashing, JWT creation, and JWT validation helpers."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from app.core.config import settings
from app.core.exceptions import InvalidTokenError
from app.models.user import User, UserRole


class PasswordService:
    """Argon2 password hashing service."""

    def __init__(self) -> None:
        self._hasher = PasswordHasher()

    def hash_password(self, password: str) -> str:
        """Hash a plain-text password."""
        return self._hasher.hash(password)

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Return true when the password matches the stored hash."""
        try:
            return self._hasher.verify(password_hash, password)
        except (VerifyMismatchError, VerificationError):
            return False


class TokenService:
    """JWT access token service."""

    def create_access_token(self, user: User) -> str:
        """Create a signed access token containing user identity claims."""
        expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        payload = {
            "sub": str(user.id),
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "exp": expires_at,
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def decode_access_token(self, token: str) -> dict:
        """Decode and validate an access token."""
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        except jwt.PyJWTError as exc:
            raise InvalidTokenError() from exc

        required_claims = {"email", "role", "exp"}
        if not required_claims.issubset(payload):
            raise InvalidTokenError()

        try:
            UUID(str(payload.get("sub") or payload.get("user_id")))
            UserRole(str(payload["role"]))
        except (ValueError, TypeError) as exc:
            raise InvalidTokenError() from exc

        return payload


password_service = PasswordService()
token_service = TokenService()
