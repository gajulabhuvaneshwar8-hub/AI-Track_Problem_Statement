"""
app/schemas/audit_log.py

Pydantic schema for audit log retrieval.
Audit logs are append-only — no create/update schema exposed via API.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    action: str
    entity_type: Optional[str]
    entity_id: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}
