# Depot — product spec

Depot is an internal inventory and orders service for a small retailer. Staff manage products, suppliers and stock; customer orders reserve stock; downstream systems are notified by webhook.

## Stack

Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, pytest + httpx, ruff, uv. SQLite in development, PostgreSQL in production. Docker for local infra. GitHub Actions for CI.

## Conventions

- `app/routers/` one file per resource, `app/services/` holds business logic and never imports FastAPI, `app/models/` and `app/schemas/` mirror each other.
- Every schema change ships with an Alembic migration.
- Every router has a test module. Existing tests are never deleted or rewritten to pass.
- `make test`, `make lint`, `make run` must always work.

## Backlog (in priority order)

| # | Story | Done when |
| --- | --- | --- |
| 0 | Project skeleton | `GET /health`; uv + pyproject; Makefile with test/lint/run; ruff; CI on every PR; one test |
| 1 | Products CRUD | `Product(sku, name, price, stock_qty)`; `/products` CRUD; 409 on duplicate sku; Alembic migration |
| 2 | Orders with stock reservation | `Order(customer_email, status, lines[])`; `pending → confirmed`, plus `cancelled`; create reserves stock, cancel releases it; 20 parallel orders against stock 10 never oversell |
| 3 | Returns | Customer requests a return on a confirmed order; staff approve or reject; approved returns restock; minimal staff page listing pending returns |

More stories (webhooks, pagination, docs) will be added as we go.