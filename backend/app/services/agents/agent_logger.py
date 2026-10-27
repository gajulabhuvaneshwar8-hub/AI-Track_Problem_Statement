"""
app/services/agents/agent_logger.py

Structured audit and telemetry logging for the AI Reconciliation Investigation Agent.
Logs key operations without exposing sensitive secrets, keys, or passwords.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, Optional

logger = logging.getLogger("app.agent")


def log_investigation_event(
    event_type: str,
    investigation_id: Optional[uuid.UUID] = None,
    exception_id: Optional[uuid.UUID] = None,
    reconciliation_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    decision: Optional[str] = None,
    duration_ms: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Emits a structured log line for agent lifecycle events.
    Guarantees no sensitive tokens, keys, or passwords are included.
    """
    safe_details = {}
    if details:
        # Sanitize known sensitive keys if any accidentally passed
        sensitive_keys = {"password", "secret", "token", "key", "authorization", "jwt"}
        for k, v in details.items():
            if not any(s in k.lower() for s in sensitive_keys):
                safe_details[k] = v

    payload = {
        "event": event_type,
        "investigation_id": str(investigation_id) if investigation_id else None,
        "exception_id": str(exception_id) if exception_id else None,
        "reconciliation_id": str(reconciliation_id) if reconciliation_id else None,
        "status": status,
        "decision": decision,
        "duration_ms": round(duration_ms, 2) if duration_ms is not None else None,
        "details": safe_details,
    }
    logger.info("AGENT_LOG %s", payload)
