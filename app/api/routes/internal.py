"""Trusted service endpoints for athlete account provisioning."""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.internal_auth import InternalServiceIdentity, require_internal_service
from app.schemas.auth import InternalAthleteUserCreate, InternalAthleteUserResponse
from app.services.invitation_service import InvitationService

router = APIRouter(prefix="/internal/v1/athlete-users", tags=["internal-athlete-users"])


@router.post("", response_model=InternalAthleteUserResponse, status_code=status.HTTP_201_CREATED)
def create_athlete_user(
    payload: InternalAthleteUserCreate,
    identity: InternalServiceIdentity = Depends(require_internal_service),
    db: Session = Depends(get_db),
) -> InternalAthleteUserResponse:
    return InvitationService(db).create_or_reuse(payload, identity.name)


@router.post("/{auth_user_id}/resend", response_model=InternalAthleteUserResponse)
def resend_invitation(
    auth_user_id: UUID,
    payload: InternalAthleteUserCreate,
    identity: InternalServiceIdentity = Depends(require_internal_service),
    db: Session = Depends(get_db),
) -> InternalAthleteUserResponse:
    return InvitationService(db).resend(auth_user_id, payload, identity.name)


@router.post("/{auth_user_id}/disable", status_code=status.HTTP_204_NO_CONTENT)
def disable_athlete_user(
    auth_user_id: UUID,
    _: InternalServiceIdentity = Depends(require_internal_service),
    db: Session = Depends(get_db),
) -> Response:
    InvitationService(db).disable(auth_user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
