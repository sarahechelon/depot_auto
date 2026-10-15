"""Shared pytest fixtures for DB-backed tests."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db import get_session, make_engine
from app.main import create_app
from app.models import order, product  # noqa: F401 - register table metadata
from app.models.base import Base

TEST_DB_FILE = "./test_depot.db"
TEST_DB_URL = f"sqlite:///{TEST_DB_FILE}"


@pytest.fixture(scope="session")
def engine():
    """Per-test-session engine; creates schema once and tears the file down."""
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    eng = make_engine(TEST_DB_URL)
    Base.metadata.create_all(bind=eng)
    try:
        yield eng
    finally:
        eng.dispose()
        if os.path.exists(TEST_DB_FILE):
            os.remove(TEST_DB_FILE)


@pytest.fixture(scope="session")
def session_factory(engine):
    """SessionLocal bound to the test engine (session-scoped)."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(autouse=True)
def _truncate_tables(engine):
    """Wipe all tables between tests so each test starts clean."""
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def session(session_factory):
    """Per-test session, rolled back and closed at teardown."""
    s = session_factory()
    try:
        yield s
    finally:
        s.rollback()
        s.close()


@pytest.fixture
def client(session_factory):
    """TestClient with `get_session` overridden to a fresh per-request session."""
    app = create_app()

    def _override():
        s = session_factory()
        try:
            yield s
        finally:
            s.rollback()
            s.close()

    app.dependency_overrides[get_session] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
