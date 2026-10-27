"""
AI Payment Reconciliation Agent — FastAPI Application Entry Point

Step 3: Full API layer with auth, merchants, transactions,
        bank transactions, settlements, exceptions, and reconciliation stubs.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings

# Route modules
from app.api.routes import health
from app.api.routes import auth
from app.api.routes import merchants
from app.api.routes import transactions
from app.api.routes import bank_transactions
from app.api.routes import settlements
from app.api.routes import exceptions
from app.api.routes import reconciliation
from app.api.routes import ingestion
from app.api.routes import ai_analysis
from app.api.routes import agents
from app.api.routes import dashboard
from app.api.routes import demo

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    logger.info("Starting AI Payment Reconciliation Agent …")

    # Auto-create tables in development (SQLite) so the app works without
    # running Alembic migrations.  For PostgreSQL in production, run Alembic
    # instead.  create_all() is safe to call repeatedly — it only creates
    # tables that do not yet exist.
    try:
        import app.models  # noqa: F401 — ensures all ORM models are registered
        from app.db.database import Base, engine
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables verified / created.")
    except Exception as exc:
        logger.error("Failed to create database tables on startup: %s", exc, exc_info=True)

    yield
    logger.info("Shutting down AI Payment Reconciliation Agent …")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        description=settings.PROJECT_DESCRIPTION,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Global exception handlers
    # ------------------------------------------------------------------
    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all: log the error but never expose internal details."""
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred. Please try again later."},
        )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    API = "/api"

    application.include_router(health.router,          prefix=API, tags=["Health"])
    application.include_router(auth.router,            prefix=API)
    application.include_router(merchants.router,       prefix=API)
    application.include_router(transactions.router,    prefix=API)
    application.include_router(bank_transactions.router, prefix=API)
    application.include_router(settlements.router,     prefix=API)
    application.include_router(exceptions.router,      prefix=API)
    application.include_router(reconciliation.router,  prefix=API)
    application.include_router(ingestion.router,       prefix=API)
    application.include_router(ai_analysis.router,     prefix=API)
    application.include_router(agents.router,          prefix=API)
    application.include_router(dashboard.router,       prefix=API)
    application.include_router(demo.router,            prefix=API)

    return application



app = create_app()
