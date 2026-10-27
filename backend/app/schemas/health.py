"""
Health check response schema.
"""

from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "service": "AI Payment Reconciliation Agent",
                "timestamp": "2024-01-01T00:00:00+00:00",
            }
        }
    }
