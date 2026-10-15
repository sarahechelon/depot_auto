UV ?= uv

.PHONY: sync migrate test lint run

sync:
	$(UV) sync --all-groups

migrate:
	$(UV) run alembic upgrade head

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .

run:
	$(UV) run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
