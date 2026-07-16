"""FastAPI dependencies for authentication and authorization."""

from collections.abc import Callable
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, InactiveUserError, InvalidTokenError
from app.core.security import token_service
from app.db.session import get_db
from app.models.user import User, UserRole, UserStatus
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Provide an auth service instance."""
    return AuthService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Resolve the authenticated user from a bearer token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise InvalidTokenError()

    payload = token_service.decode_access_token(credentials.credentials)
    user = auth_service.get_user_by_id(UUID(str(payload["user_id"])))

    if user is None:
        raise InvalidTokenError()
    if not user.is_active or user.status != UserStatus.ACTIVE:
        raise InactiveUserError()

    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Return a dependency that enforces one of the allowed user roles."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError()
        return current_user

    return role_checker
