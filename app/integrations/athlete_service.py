"""Internal Athlete Service callback used after invitation acceptance."""

from uuid import UUID

import httpx

from app.core.config import settings
from app.core.exceptions import UpstreamServiceError


class AthleteServiceClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=settings.upstream_timeout_seconds)

    def activate_link(self, auth_user_id: UUID) -> None:
        try:
            response = self.client.post(
                f"{settings.athlete_service_internal_url.rstrip('/')}/internal/v1/"
                f"athlete-user-links/{auth_user_id}/activate",
                headers={
                    "X-Service-Name": settings.internal_service_name,
                    "X-Service-Token": settings.internal_service_token,
                },
            )
        except httpx.HTTPError as exc:
            raise UpstreamServiceError("Athlete Service activation callback failed.") from exc
        if response.status_code not in {200, 204}:
            raise UpstreamServiceError("Athlete Service activation callback failed.")
