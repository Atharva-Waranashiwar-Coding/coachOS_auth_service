"""Domain exceptions and centralized FastAPI exception handlers."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error with an HTTP mapping."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    code = "internal_error"
    message = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class DuplicateEmailError(AppError):
    """Raised when a user tries to register an email that already exists."""

    status_code = status.HTTP_409_CONFLICT
    code = "duplicate_email"
    message = "A user with this email already exists."


class InvalidCredentialsError(AppError):
    """Raised when login credentials are invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "invalid_credentials"
    message = "Invalid email or password."


class InvalidTokenError(AppError):
    """Raised when a JWT is missing, malformed, expired, or invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "invalid_token"
    message = "Invalid or expired access token."


class InactiveUserError(AppError):
    """Raised when an authenticated user is disabled."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "inactive_user"
    message = "User account is inactive."


class ForbiddenError(AppError):
    """Raised when a user lacks the required role."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"
    message = "You do not have permission to access this resource."


class InvitationError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "invalid_invitation"
    message = "Invitation is invalid, expired, or already used."


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    message = "The request conflicts with existing account state."


class RateLimitError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"
    message = "Too many invitation requests. Try again later."


class UpstreamServiceError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "upstream_service_unavailable"
    message = "A required service is unavailable."


def _error_response(status_code: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    """Build a consistent error response envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach centralized exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "loc": error.get("loc", []),
                "msg": error.get("msg", "Invalid value."),
                "type": error.get("type", "value_error"),
            }
            for error in exc.errors()
        ]
        return _error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_error",
            "One or more fields are invalid.",
            {"errors": errors},
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(_: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("Database error", exc_info=exc)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "database_error",
            "A database error occurred.",
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return _error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "An unexpected error occurred.",
        )
