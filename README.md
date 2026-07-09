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

## Planned API

- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/refresh`

## Testing

```bash
pytest
```

## Status

Stage 0: service skeleton created. Auth models, routes, JWT handling, and tests are next.
