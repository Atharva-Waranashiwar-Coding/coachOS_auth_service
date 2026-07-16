"""FastAPI application entry point for the auth service."""

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="CoachOS Auth Service")
register_exception_handlers(app)
app.include_router(api_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Return service health and environment metadata."""
    return {
        "status": "ok",
        "service": "auth",
        "environment": settings.environment,
    }
