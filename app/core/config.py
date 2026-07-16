"""Application configuration loaded from environment variables."""

import json
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the auth service."""

    app_name: str = Field(default="coachos-auth-service", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    database_url: str = Field(alias="DATABASE_URL")
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
        gt=0,
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: list[str] = Field(default_factory=list, alias="CORS_ORIGINS")
    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")
    request_id_header: str = Field(default="X-Request-ID", alias="REQUEST_ID_HEADER")
    internal_service_tokens: dict[str, str] = Field(default_factory=dict, alias="INTERNAL_SERVICE_TOKENS")
    athlete_invitation_expiration_hours: int = Field(
        default=48, alias="ATHLETE_INVITATION_EXPIRATION_HOURS", gt=0, le=168
    )
    athlete_invitation_base_url: str = Field(
        default="http://localhost:5173/invitations/accept", alias="ATHLETE_INVITATION_BASE_URL"
    )
    allow_dev_invitation_url_response: bool = Field(default=True, alias="ALLOW_DEV_INVITATION_URL_RESPONSE")
    max_invitation_resends_per_hour: int = Field(default=3, alias="MAX_INVITATION_RESENDS_PER_HOUR", gt=0, le=20)
    athlete_service_internal_url: str = Field(default="http://localhost:8002", alias="ATHLETE_SERVICE_INTERNAL_URL")
    internal_service_name: str = Field(default="auth-service", alias="INTERNAL_SERVICE_NAME")
    internal_service_token: str = Field(default="", alias="INTERNAL_SERVICE_TOKEN")
    upstream_timeout_seconds: float = Field(default=5, alias="UPSTREAM_TIMEOUT_SECONDS", gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("internal_service_tokens", mode="before")
    @classmethod
    def parse_internal_tokens(cls, value: str | dict[str, str]) -> dict[str, str]:
        if isinstance(value, str):
            parsed = json.loads(value)
            if not isinstance(parsed, dict) or not all(
                isinstance(key, str) and isinstance(token, str) for key, token in parsed.items()
            ):
                raise ValueError("INTERNAL_SERVICE_TOKENS must be a JSON object of strings")
            return parsed
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
