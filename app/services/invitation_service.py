"""Internally controlled athlete account invitation lifecycle."""

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ConflictError, InvitationError, RateLimitError
from app.core.security import password_service
from app.integrations.athlete_service import AthleteServiceClient
from app.models.user import AccountInvitation, User, UserRole, UserStatus
from app.schemas.auth import (
    InternalAthleteUserCreate,
    InternalAthleteUserResponse,
    InvitationAcceptRequest,
)

logger = logging.getLogger(__name__)


def hash_invitation_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class InvitationService:
    def __init__(self, db: Session, athlete_service: AthleteServiceClient | None = None) -> None:
        self.db = db
        self.athlete_service = athlete_service or AthleteServiceClient()

    def create_or_reuse(self, payload: InternalAthleteUserCreate, caller_service: str) -> InternalAthleteUserResponse:
        email = payload.email.lower()
        user = self.db.scalar(select(User).where(User.email == email))
        if user and user.role != UserRole.ATHLETE:
            raise ConflictError("Email belongs to a non-athlete account.")
        if user and user.status == UserStatus.DISABLED:
            raise ConflictError("Athlete account is disabled.")
        if user and user.status == UserStatus.ACTIVE:
            return InternalAthleteUserResponse(
                auth_user_id=user.id,
                user_status=user.status,
                invitation_id=None,
            )
        if user is None:
            user = User(
                email=email,
                password_hash=None,
                role=UserRole.ATHLETE,
                status=UserStatus.PENDING,
                is_active=False,
                is_verified=False,
            )
            self.db.add(user)
            self.db.flush()
        invitation, raw_token = self._issue(user, payload.athlete_id, caller_service)
        self.db.commit()
        logger.info(
            "Athlete invitation created",
            extra={"user_id": str(user.id), "invitation_id": str(invitation.id)},
        )
        return self._response(user, invitation, raw_token)

    def resend(
        self,
        auth_user_id: UUID,
        payload: InternalAthleteUserCreate,
        caller_service: str,
    ) -> InternalAthleteUserResponse:
        user = self.db.get(User, auth_user_id)
        if not user or user.role != UserRole.ATHLETE or user.email != payload.email.lower():
            raise InvitationError()
        if user.status != UserStatus.PENDING:
            raise ConflictError("Only pending athlete invitations can be resent.")
        invitation, raw_token = self._issue(user, payload.athlete_id, caller_service)
        self.db.commit()
        return self._response(user, invitation, raw_token)

    def accept(self, payload: InvitationAcceptRequest) -> User:
        now = datetime.now(UTC)
        invitation = self.db.scalar(
            select(AccountInvitation).where(AccountInvitation.token_hash == hash_invitation_token(payload.token))
        )
        expires_at = (
            invitation.expires_at.replace(tzinfo=UTC)
            if invitation and invitation.expires_at.tzinfo is None
            else invitation.expires_at if invitation else None
        )
        if not invitation or invitation.used_at or not expires_at or expires_at <= now:
            raise InvitationError()
        user = self.db.get(User, invitation.user_id)
        if not user or user.role != UserRole.ATHLETE or user.status != UserStatus.PENDING:
            raise InvitationError()

        user.password_hash = password_service.hash_password(payload.password)
        user.status = UserStatus.ACTIVE
        user.is_active = True
        user.is_verified = True
        invitation.used_at = now
        self.athlete_service.activate_link(user.id)
        self.db.commit()
        self.db.refresh(user)
        logger.info("Athlete invitation accepted", extra={"user_id": str(user.id)})
        return user

    def disable(self, auth_user_id: UUID) -> None:
        user = self.db.get(User, auth_user_id)
        if not user or user.role != UserRole.ATHLETE:
            raise InvitationError()
        user.status = UserStatus.DISABLED
        user.is_active = False
        self.db.commit()
        logger.info("Athlete account disabled", extra={"user_id": str(user.id)})

    def _issue(self, user: User, athlete_id: UUID, caller_service: str) -> tuple[AccountInvitation, str]:
        now = datetime.now(UTC)
        count = (
            self.db.scalar(
                select(func.count(AccountInvitation.id)).where(
                    AccountInvitation.user_id == user.id,
                    AccountInvitation.created_at >= now - timedelta(hours=1),
                )
            )
            or 0
        )
        if count >= settings.max_invitation_resends_per_hour:
            raise RateLimitError()
        for existing in self.db.scalars(
            select(AccountInvitation).where(
                AccountInvitation.user_id == user.id,
                AccountInvitation.used_at.is_(None),
            )
        ):
            existing.used_at = now
        raw_token = secrets.token_urlsafe(48)
        invitation = AccountInvitation(
            user_id=user.id,
            athlete_reference_id=athlete_id,
            token_hash=hash_invitation_token(raw_token),
            expires_at=now + timedelta(hours=settings.athlete_invitation_expiration_hours),
            created_by_service=caller_service,
        )
        self.db.add(invitation)
        self.db.flush()
        return invitation, raw_token

    @staticmethod
    def _response(user: User, invitation: AccountInvitation, raw_token: str) -> InternalAthleteUserResponse:
        allow_url = settings.environment != "production" and settings.allow_dev_invitation_url_response
        url = f"{settings.athlete_invitation_base_url}?token={raw_token}" if allow_url else None
        return InternalAthleteUserResponse(
            auth_user_id=user.id,
            user_status=user.status,
            invitation_id=invitation.id,
            development_invitation_url=url,
        )
