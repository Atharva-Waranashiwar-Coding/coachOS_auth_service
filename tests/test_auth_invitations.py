"""Auth and athlete invitation workflow tests."""

import os
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("INTERNAL_SERVICE_TOKENS", '{"athlete-service":"athlete-token"}')
os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "auth-token")
os.environ.setdefault("ALLOW_DEV_INVITATION_URL_RESPONSE", "true")

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.integrations.athlete_service import AthleteServiceClient  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import AccountInvitation, User, UserRole, UserStatus  # noqa: E402
from app.services.invitation_service import hash_invitation_token  # noqa: E402

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
def database() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def session() -> Session:
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(session: Session, monkeypatch) -> TestClient:
    def override_db():
        yield session

    monkeypatch.setattr(AthleteServiceClient, "activate_link", lambda self, auth_user_id: None)
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def internal_headers(token: str = "athlete-token") -> dict[str, str]:
    return {"X-Service-Name": "athlete-service", "X-Service-Token": token}


def invitation_request(email: str = "athlete@example.com") -> dict[str, str]:
    return {
        "email": email,
        "athlete_id": str(uuid4()),
        "invited_by_user_id": str(uuid4()),
    }


def raw_token(response: dict) -> str:
    url = response["development_invitation_url"]
    return parse_qs(urlparse(url).query)["token"][0]


def test_public_signup_is_coach_only_and_rejects_role_selection(client: TestClient) -> None:
    rejected = client.post(
        "/auth/signup",
        json={"email": "athlete@example.com", "password": "secure-password", "role": "athlete"},
    )
    created = client.post(
        "/auth/signup",
        json={"email": "coach@example.com", "password": "secure-password"},
    )

    assert rejected.status_code == 422
    assert created.status_code == 201
    assert created.json()["role"] == "coach"
    assert created.json()["status"] == "active"


def test_internal_creation_requires_valid_service_token(client: TestClient) -> None:
    response = client.post(
        "/internal/v1/athlete-users",
        json=invitation_request(),
        headers=internal_headers("wrong"),
    )

    assert response.status_code == 401


def test_internal_creation_stores_only_token_hash(client: TestClient, session: Session) -> None:
    response = client.post(
        "/internal/v1/athlete-users",
        json=invitation_request(),
        headers=internal_headers(),
    )
    body = response.json()
    token = raw_token(body)
    invitation = session.scalar(select(AccountInvitation))
    user = session.get(User, UUID(body["auth_user_id"]))

    assert response.status_code == 201
    assert user is not None
    assert user.role == UserRole.ATHLETE
    assert user.status == UserStatus.PENDING
    assert user.password_hash is None
    assert invitation is not None
    assert invitation.token_hash == hash_invitation_token(token)
    assert token not in invitation.token_hash


def test_accept_invitation_activates_athlete_and_supports_login(client: TestClient, session: Session) -> None:
    created = client.post(
        "/internal/v1/athlete-users",
        json=invitation_request(),
        headers=internal_headers(),
    ).json()
    token = raw_token(created)
    accepted = client.post(
        "/auth/invitations/accept",
        json={
            "token": token,
            "password": "athlete-password",
            "password_confirmation": "athlete-password",
        },
    )
    login = client.post(
        "/auth/login",
        json={"email": "athlete@example.com", "password": "athlete-password"},
    )
    invitation = session.get(AccountInvitation, UUID(created["invitation_id"]))

    assert accepted.status_code == 200
    assert accepted.json()["user"]["status"] == "active"
    assert login.status_code == 200
    assert login.json()["user"]["role"] == "athlete"
    assert invitation is not None and invitation.used_at is not None
    assert "sub" in __import__("jwt").decode(login.json()["access_token"], "test-secret", algorithms=["HS256"])


def test_used_and_expired_invitations_are_rejected(client: TestClient, session: Session) -> None:
    created = client.post(
        "/internal/v1/athlete-users",
        json=invitation_request(),
        headers=internal_headers(),
    ).json()
    token = raw_token(created)
    payload = {
        "token": token,
        "password": "athlete-password",
        "password_confirmation": "athlete-password",
    }
    assert client.post("/auth/invitations/accept", json=payload).status_code == 200
    assert client.post("/auth/invitations/accept", json=payload).status_code == 400

    second = client.post(
        "/internal/v1/athlete-users",
        json=invitation_request("second@example.com"),
        headers=internal_headers(),
    ).json()
    invitation = session.get(AccountInvitation, UUID(second["invitation_id"]))
    assert invitation is not None
    invitation.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    session.commit()
    expired = client.post(
        "/auth/invitations/accept",
        json={
            "token": raw_token(second),
            "password": "athlete-password",
            "password_confirmation": "athlete-password",
        },
    )
    assert expired.status_code == 400


def test_resend_invalidates_previous_token(client: TestClient, session: Session) -> None:
    request = invitation_request()
    first = client.post(
        "/internal/v1/athlete-users",
        json=request,
        headers=internal_headers(),
    ).json()
    second = client.post(
        f"/internal/v1/athlete-users/{first['auth_user_id']}/resend",
        json=request,
        headers=internal_headers(),
    ).json()

    old_invitation = session.get(AccountInvitation, UUID(first["invitation_id"]))
    assert old_invitation is not None and old_invitation.used_at is not None
    rejected = client.post(
        "/auth/invitations/accept",
        json={
            "token": raw_token(first),
            "password": "athlete-password",
            "password_confirmation": "athlete-password",
        },
    )
    accepted = client.post(
        "/auth/invitations/accept",
        json={
            "token": raw_token(second),
            "password": "athlete-password",
            "password_confirmation": "athlete-password",
        },
    )
    assert rejected.status_code == 400
    assert accepted.status_code == 200


def test_password_confirmation_and_disabled_login(client: TestClient, session: Session) -> None:
    created = client.post(
        "/internal/v1/athlete-users",
        json=invitation_request(),
        headers=internal_headers(),
    ).json()
    mismatch = client.post(
        "/auth/invitations/accept",
        json={
            "token": raw_token(created),
            "password": "athlete-password",
            "password_confirmation": "different-password",
        },
    )
    assert mismatch.status_code == 422

    user = session.get(User, UUID(created["auth_user_id"]))
    assert user is not None
    user.password_hash = __import__("app.core.security", fromlist=["password_service"]).password_service.hash_password(
        "athlete-password"
    )
    user.status = UserStatus.DISABLED
    user.is_active = False
    session.commit()
    login = client.post(
        "/auth/login",
        json={"email": "athlete@example.com", "password": "athlete-password"},
    )
    assert login.status_code == 403
