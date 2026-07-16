"""Authentication API routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_auth_service, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    InvitationAcceptRequest,
    InvitationAcceptResponse,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.services.auth_service import AuthService
from app.services.invitation_service import InvitationService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, auth_service: AuthService = Depends(get_auth_service)) -> User:
    """Register a new user and return public user details."""
    return auth_service.signup(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, auth_service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    """Authenticate a user and return a JWT access token."""
    return auth_service.login(payload)


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Return the currently authenticated user."""
    return current_user


@router.post("/invitations/accept", response_model=InvitationAcceptResponse)
def accept_invitation(
    payload: InvitationAcceptRequest,
    db: Session = Depends(get_db),
) -> InvitationAcceptResponse:
    return InvitationAcceptResponse(user=UserRead.model_validate(InvitationService(db).accept(payload)))
