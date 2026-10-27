"""
tests/conftest.py

Shared pytest fixtures for ALL tests:
  - Unit/model tests: `engine` + `session` (SQLite in-memory, per-test rollback)
  - API tests:        `client` (FastAPI TestClient with DB override)

Both use the same SQLite in-memory setup — no Postgres required.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# Shared SQLite engine  (session-scoped so schema is created once)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite://"  # pure in-memory


@pytest.fixture(scope="session")
def engine():
    """Session-scoped in-memory SQLite engine — schema created once per session."""
    _engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Populate metadata from all models
    import app.models  # noqa: F401

    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)
    _engine.dispose()


# ---------------------------------------------------------------------------
# Unit / model test session  (function-scoped, rolled back after each test)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def session(engine) -> Session:
    """
    Transactional session for model-level unit tests.
    Changes are rolled back after each test for isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()
    _session = sessionmaker(bind=connection, autocommit=False, autoflush=False)()

    yield _session

    _session.close()
    try:
        transaction.rollback()
    except Exception:
        pass
    connection.close()


# ---------------------------------------------------------------------------
# API test fixtures
# ---------------------------------------------------------------------------

TestingSessionLocal = None  # lazily created after engine fixture runs


@pytest.fixture(scope="function")
def db_session(engine) -> Session:
    """
    Function-scoped SQLAlchemy session for API tests.
    Each test gets a fresh connection; rolled back on teardown.
    """
    connection = engine.connect()
    transaction = connection.begin()
    _session = sessionmaker(bind=connection, autocommit=False, autoflush=False)()

    yield _session

    _session.close()
    try:
        transaction.rollback()
    except Exception:
        pass
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session):
    """
    FastAPI TestClient with the production DB dependency overridden
    to use the in-memory SQLite session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def auth_headers(client):
    """
    Register + login a test admin user; return Authorization headers.
    Used by API tests that require authentication.
    """
    client.post(
        "/api/auth/register",
        json={
            "name": "Test Admin",
            "email": "admin@testexample.com",
            "password": "TestP@ss123",
            "role": "admin",
        },
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "admin@testexample.com", "password": "TestP@ss123"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
