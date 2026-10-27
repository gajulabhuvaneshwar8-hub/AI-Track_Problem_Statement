"""
Database session factory and declarative base.
Only configuration is set up here — no business tables.

Supports both SQLite (local dev, no server required) and PostgreSQL (production).
The DATABASE_URL in .env controls which is used.
"""

import logging

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine — dialect-aware creation
# ---------------------------------------------------------------------------
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    # SQLite does not support pool_size / max_overflow; use the default
    # NullPool or SingletonThreadPool depending on the URL.
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=(settings.ENVIRONMENT == "development"),
    )

    # SQLite requires explicit PRAGMA to enforce foreign keys
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    logger.info("Using SQLite database: %s", settings.DATABASE_URL)
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,   # verify connections before use
        pool_size=10,
        max_overflow=20,
        echo=(settings.ENVIRONMENT == "development"),
    )
    logger.info("Using PostgreSQL database")


# ---------------------------------------------------------------------------
# Declarative Base — all models inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Dependency helper (used by FastAPI Depends)
# ---------------------------------------------------------------------------
def get_db():
    """Yield a database session and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
