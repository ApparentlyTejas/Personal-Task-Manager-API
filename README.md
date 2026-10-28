# Personal Task Manager API

![CI](https://github.com/ApparentlyTejas/Personal-Task-Manager-API/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-async-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/docker-compose-2496ED?logo=docker&logoColor=white)

An async REST API for managing tasks (create, list, fetch, update, delete), built with FastAPI and PostgreSQL. SQLAlchemy's async engine talks to Postgres over `asyncpg`, so a request never blocks the event loop while waiting on the database. The whole stack (API + Postgres) runs with one `docker compose up` command, and the project ships with a pytest suite that runs against a real Postgres instance in CI.

## Request flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI as FastAPI (main.py)
    participant Session as AsyncSession (database.py)
    participant Postgres

    Client->>FastAPI: HTTP request (e.g. POST /tasks)
    FastAPI->>FastAPI: Validate body with Pydantic (TaskCreate/TaskUpdate)
    FastAPI->>Session: Depends(get_session)
    Session->>Postgres: await session.execute(...) via asyncpg
    Postgres-->>Session: rows
    Session-->>FastAPI: ORM objects (TaskDB)
    FastAPI-->>Client: JSON response (TaskResponse)
```

## Features

- Full CRUD on tasks: `POST`, `GET` (list and by id), `PATCH`, `DELETE`
- Fully async request path: FastAPI route handlers, SQLAlchemy's `AsyncSession`, and the `asyncpg` driver, no blocking database calls
- Request and response validation with Pydantic models (`TaskCreate`, `TaskUpdate`, `TaskResponse`), separate from the SQLAlchemy ORM model (`TaskDB`)
- Partial updates: `PATCH /tasks/{id}` only touches the fields you send, via `model_dump(exclude_unset=True)`
- Proper error handling (404 for missing tasks, 422 for validation errors)
- Tables created automatically on startup through a FastAPI `lifespan` hook
- One-command local stack with Docker Compose (API container + Postgres container with a health check gate)
- CI pipeline (GitHub Actions) running ruff, mypy, and pytest with coverage against a real Postgres service container

## Tech stack

| Layer | Choice |
|---|---|
| Framework | FastAPI |
| Language | Python 3.11 |
| ORM | SQLAlchemy 2.0 (async) |
| Database driver | asyncpg |
| Database | PostgreSQL 15 |
| Server | Uvicorn |
| Validation | Pydantic 2 |
| Containerization | Docker, Docker Compose |
| Testing | pytest, pytest-asyncio, coverage.py |
| Linting / typing | ruff, mypy |
| CI | GitHub Actions |

## Data model

The `tasks` table (`models.py`):

| Column | Type | Notes |
|---|---|---|
| `id` | integer | primary key, auto-increment |
| `title` | varchar(255) | required |
| `description` | text | optional |
| `status` | varchar(50) | free-form string, defaults to `pending` |
| `created_at` | timestamptz | set by the database on insert |

## Running it locally

### With Docker (recommended)

```bash
git clone https://github.com/ApparentlyTejas/Personal-Task-Manager-API.git
cd Personal-Task-Manager-API
docker compose up --build
```

This starts two containers: `task_manager_db` (Postgres, host port 5433) and `task_manager_app` (FastAPI, host port 8001). The app container waits for Postgres's health check before starting.

```bash
curl http://localhost:8001/
# {"message":"Task Manager API is running! 🚀"}
```

### Without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Point at your own Postgres instance
export DATABASE_URL="postgresql+asyncpg://taskuser:taskpass@localhost:5432/taskdb"

uvicorn main:app --reload
```

Interactive docs are available at `/docs` (Swagger) and `/redoc` once the server is running.

## Example request

```bash
curl -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Write project README", "description": "Document the API for recruiters", "status": "in_progress"}'
```

Response:

```json
{
  "id": 1,
  "title": "Write project README",
  "description": "Document the API for recruiters",
  "status": "in_progress",
  "created_at": "2026-05-21T20:30:00+00:00"
}
```

Fetching it back:

```bash
curl http://localhost:8001/tasks/1
```

```json
{
  "id": 1,
  "title": "Write project README",
  "description": "Document the API for recruiters",
  "status": "in_progress",
  "created_at": "2026-05-21T20:30:00+00:00"
}
```

Updating just the status, leaving everything else untouched:

```bash
curl -X PATCH http://localhost:8001/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

## Testing

The test suite (`tests/test_smoke.py` and `tests/test_tasks.py`) runs with pytest against a real Postgres database, not a mock. It covers the health check, a full CRUD round-trip, 404s on every not-found path, 422s on validation errors (missing, null, or wrong-typed fields), partial-update behavior (confirming `PATCH` leaves unset fields alone), multi-row listing and deletion, and edge cases like empty titles and the 255-character column boundary on `title`. Coverage sits at 98% across `main.py`, `models.py`, and `database.py`.

To run it locally:

```bash
pip install -r requirements-dev.txt

docker run -d --name taskdb-test -e POSTGRES_USER=taskuser -e POSTGRES_PASSWORD=taskpass \
  -e POSTGRES_DB=taskdb -p 5544:5432 postgres:15-alpine

DATABASE_URL="postgresql+asyncpg://taskuser:taskpass@localhost:5544/taskdb" \
  pytest --cov=main --cov=models --cov=database --cov-report=term-missing
```

Every push and pull request to `main` also runs ruff and mypy in CI, alongside the test job, see `.github/workflows/ci.yml`.

## Possible next steps

- Authentication (JWT)
- Filtering, sorting, and pagination on `GET /tasks`
- A proper status enum with transition rules, instead of a free-form string
- Deployment to a cloud provider

## License

MIT. See `LICENSE`.

## Author

**Tejas Malhotra**
GitHub: [ApparentlyTejas](https://github.com/ApparentlyTejas)
