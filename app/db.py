"""Database session management."""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base


def database_url() -> str:
    """Resolve the database URL from env or default to local SQLite file."""
    return os.environ.get("DATABASE_URL", "sqlite:///./depot.db")


def _register_sqlite_pragma(eng: Engine) -> Engine:
    """Enable SQLite foreign-key enforcement at connection open.

    SQLite ignores FK constraints by default; without this, deleting a
    product referenced by an order_line would silently succeed and leave a
    dangling row.
    """
    if eng.dialect.name != "sqlite":
        return eng

    @event.listens_for(eng, "connect")
    def _enable_fk(dbapi_connection, _connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return eng


def make_engine(url: str | None = None) -> Engine:
    """Build an Engine with engine-specific tuning applied."""
    return _register_sqlite_pragma(
        create_engine(url or database_url(), future=True, echo=False),
    )


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    """Create all tables (test/dev convenience; production uses Alembic)."""
    Base.metadata.create_all(bind=engine)
