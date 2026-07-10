# CoachOS Auth Service

Authentication and authorization service for CoachOS.

## Responsibilities

- Coach signup and login
- Athlete authentication support later
- Password hashing and credential validation
- JWT access token generation
- User role claims
- Protected identity endpoint

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

Stage 1: signup, login, JWT access tokens, protected user lookup, database model, and Alembic migration are implemented. Refresh tokens, OAuth, password reset, email verification, MFA, and tests are next.
