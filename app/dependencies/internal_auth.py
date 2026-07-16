"""Authentication for trusted service-to-service Auth API calls."""

import hmac
from dataclasses import dataclass

from fastapi import Header

from app.core.config import settings
from app.core.exceptions import InvalidTokenError


@dataclass(frozen=True)
class InternalServiceIdentity:
    name: str


def require_internal_service(
    x_service_name: str | None = Header(default=None),
    x_service_token: str | None = Header(default=None),
) -> InternalServiceIdentity:
    if not x_service_name or not x_service_token:
        raise InvalidTokenError("Internal service authentication is required.")
    expected = settings.internal_service_tokens.get(x_service_name)
    if not expected or not hmac.compare_digest(expected, x_service_token):
        raise InvalidTokenError("Invalid internal service credentials.")
    return InternalServiceIdentity(x_service_name)
