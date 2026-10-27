"""
app/services/audit_service.py

Database operations for the AuditLog entity.
Audit logs are append-only — no update or delete.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def create_audit_log(
    db: Session,
    *,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Append an immutable audit event."""
    log = AuditLog(
        id=uuid.uuid4(),
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def list_audit_logs(
    db: Session,
    *,
    user_id: Optional[uuid.UUID] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Tuple[List[AuditLog], int]:
    """List audit logs with optional filters."""
    query = db.query(AuditLog)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if entity_type is not None:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action is not None:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    items = (
        query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    )
    return items, total
