"""Database session management."""

import os
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base


def database_url() -> str:
    """Resolve the database URL from env or default to local SQLite file."""
    return os.environ.get("DATABASE_URL", "sqlite:///./depot.db")


engine = create_engine(database_url(), future=True, echo=False)
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
