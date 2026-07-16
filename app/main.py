"""FastAPI application entry point for the auth service."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.observability import register_observability
from app.db.session import SessionLocal

configure_logging()

app = FastAPI(title="CoachOS Auth Service")
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
register_observability(app)
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


@app.get("/health/live", tags=["health"])
def live_check() -> dict[str, str]:
    """Return process liveness without checking dependencies."""
    return {"status": "ok", "service": "auth"}


@app.get("/health/ready", tags=["health"])
def ready_check() -> dict[str, str]:
    """Return readiness after verifying the service database."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database is unavailable.") from exc
    return {"status": "ready", "service": "auth", "database": "ok"}
