# CoachOS Auth Service

Authentication and authorization service for CoachOS.

## Responsibilities

- Coach public signup and coach/athlete login
- Controlled athlete account invitations and activation
- Password hashing and credential validation
- JWT access token generation
- User role claims
- Protected identity endpoint
- Pending, active, and disabled account states

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker

## Project Structure

- `app/api`: API route modules
- `app/core`: configuration and security helpers
- `app/db`: database connection and session setup
- `app/models`: database models
- `app/schemas`: request and response schemas
- `app/services`: auth business logic
- `app/utils`: shared utilities
- `alembic`: database migrations
- `tests`: service tests

## Environment

Copy `.env.example` to `.env` for local development. Do not commit `.env`.

Required values:

- `APP_NAME`
- `ENVIRONMENT`
- `DATABASE_URL`

## Running Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The service exposes:

- Local app: `http://localhost:8000`
- Docker Compose port: `http://localhost:8001`
- Health check: `GET /health`

## Docker

```bash
docker compose up --build
```

## API

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/invitations/accept`
- `POST /internal/v1/athlete-users`
- `POST /internal/v1/athlete-users/{auth_user_id}/resend`
- `POST /internal/v1/athlete-users/{auth_user_id}/disable`

Public signup always creates a coach account and rejects role selection or athlete profile references. Athlete identities are created only through the authenticated Athlete Service internal API. Invitation tokens are cryptographically random, stored only as SHA-256 hashes, expire, are single-use, and are invalidated on resend. Development invitation URLs are returned only outside production when explicitly enabled.

Accepting an invitation validates password confirmation, activates the pending athlete user, marks the token used, and calls the Athlete Service activation callback before committing. Disabled and pending accounts cannot log in.

Future endpoints:

- `POST /auth/refresh`
- `POST /auth/password-reset`
- OAuth provider callbacks
- Email verification endpoints
- MFA enrollment and challenge endpoints

## Testing

```bash
pytest
```

## Status

Coach signup, role-aware login, JWT access tokens, protected user lookup, athlete invitations, activation callbacks, account disablement, Alembic migrations, and automated tests are implemented. Refresh tokens, OAuth, password reset, email verification, MFA, production email delivery, and distributed rate limiting remain future work.
