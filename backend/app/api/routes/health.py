"""
Health check endpoint.
No business logic here — kept intentionally minimal.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="API health check")
async def health_check() -> HealthResponse:
    """
    Returns service status.
    Used by the frontend to verify backend connectivity.
    """
    logger.debug("Health check requested")
    return HealthResponse(
        status="ok",
        service="AI Payment Reconciliation Agent",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
