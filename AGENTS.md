# AGENTS.md — how to work in this repo

Conventions from `docs/SPEC.md`. Follow them every session.

## Stack
Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, pytest + httpx,
ruff, uv. SQLite in dev, PostgreSQL in prod. Docker for local infra. GitHub
Actions for CI.

## Layout
- `app/routers/` — one file per resource, HTTP-only.
- `app/services/` — business logic. **Never import FastAPI.**
- `app/models/` — SQLAlchemy 2.0 ORM models.
- `app/schemas/` — Pydantic v2 request/response models, mirror `app/models/`.

## Rules
- Every schema/model change ships with an Alembic migration in the same PR.
- Every router has a matching test module under `tests/`. Mirror the router
  filename.
- Never delete or rewrite existing tests to make them pass. Add new ones
  alongside.
- `make test`, `make lint`, `make run` must always succeed on `master`.

## Workflow
- Work the backlog in `docs/SPEC.md` in priority order, one story per PR.
- Run `make lint && make test` before each commit.
- Smallest diff per PR; no drive-by changes.
