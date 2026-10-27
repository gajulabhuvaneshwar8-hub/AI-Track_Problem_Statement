"""
app/services/exception_service.py

Comprehensive service layer managing reconciliation exceptions, human-in-the-loop
workflows, lifecycle state transitions, audit logging, and timeline aggregation.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models.agent_investigation import AgentInvestigation
from app.models.ai_analysis import AIAnalysis
from app.models.audit_log import AuditLog
from app.models.enums import ExceptionSeverity, ExceptionStatus
from app.models.exception import PaymentException
from app.models.reconciliation_result import ReconciliationResult
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.exception import (
    ExceptionCreate,
    ExceptionDetailedResponse,
    ExceptionResponse,
    ExceptionUpdate,
    ExceptionWorkflowSummary,
    TimelineEvent,
)
from app.services.audit_service import create_audit_log

logger = logging.getLogger(__name__)


def _sanitize_string(val: Optional[str]) -> Optional[str]:
    """Helper to strip whitespace or return None."""
    if val is None:
        return None
    trimmed = val.strip()
    return trimmed if trimmed else None


def _enrich_exception_response(exc: PaymentException) -> ExceptionResponse:
    """Helper to convert PaymentException ORM object to ExceptionResponse with derived attributes."""
    recon = exc.reconciliation_result
    txn = recon.transaction if recon else None
    bank_txn = recon.bank_transaction if recon else None

    # Determine amount & currency safely
    amount = None
    currency = "INR"
    if recon and recon.difference_amount is not None:
        amount = recon.difference_amount
    elif txn and txn.amount is not None:
        amount = txn.amount
    elif bank_txn and bank_txn.amount is not None:
        amount = bank_txn.amount

    if txn and txn.currency:
        currency = txn.currency
    elif bank_txn and bank_txn.currency:
        currency = bank_txn.currency

    assignee_name = exc.assignee.name if exc.assignee else None

    return ExceptionResponse(
        id=exc.id,
        reconciliation_id=exc.reconciliation_id,
        merchant_id=exc.merchant_id,
        severity=exc.severity,
        category=exc.category,
        title=exc.title,
        description=exc.description,
        recommended_action=exc.recommended_action,
        status=exc.status,
        assigned_to=exc.assigned_to,
        assignee_name=assignee_name,
        resolved_by=exc.resolved_by,
        ignored_by=exc.ignored_by,
        resolution_note=exc.resolution_note,
        reviewer_note=exc.reviewer_note,
        escalation_reason=exc.escalation_reason,
        resolved_at=exc.resolved_at,
        ignored_at=exc.ignored_at,
        escalated_at=exc.escalated_at,
        updated_at=exc.updated_at,
        created_at=exc.created_at,
        amount=amount,
        currency=currency,
    )


def create_exception(
    db: Session,
    payload: ExceptionCreate,
    current_user: Optional[User] = None,
) -> PaymentException:
    """Create and persist a new PaymentException ticket with audit logging."""
    data = payload.model_dump()
    merchant_id = data.get("merchant_id")

    # If merchant_id not supplied, attempt to infer from reconciliation_result
    if not merchant_id and data.get("reconciliation_id"):
        recon = db.get(ReconciliationResult, data["reconciliation_id"])
        if recon:
            if recon.transaction and recon.transaction.merchant_id:
                merchant_id = recon.transaction.merchant_id
            elif recon.bank_transaction and recon.bank_transaction.merchant_id:
                merchant_id = recon.bank_transaction.merchant_id
            data["merchant_id"] = merchant_id

    exc = PaymentException(id=uuid.uuid4(), **data)
    db.add(exc)
    db.commit()
    db.refresh(exc)

    create_audit_log(
        db,
        action="exception_created",
        user_id=current_user.id if current_user else None,
        entity_type="exception",
        entity_id=str(exc.id),
        details={
            "title": exc.title,
            "severity": exc.severity.value,
            "category": exc.category,
            "status": exc.status.value,
        },
    )

    logger.info("Created exception %s severity=%s", exc.id, exc.severity.value)
    return exc


def get_exception(db: Session, exception_id: uuid.UUID) -> Optional[PaymentException]:
    """Retrieve exception by primary key."""
    return db.get(PaymentException, exception_id)


def list_exceptions(
    db: Session,
    *,
    severity: Optional[ExceptionSeverity] = None,
    category: Optional[str] = None,
    status: Optional[ExceptionStatus] = None,
    assigned_to: Optional[uuid.UUID] = None,
    merchant_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[PaymentException], int]:
    """Query exceptions with rich filtering, searching, and pagination."""
    query = db.query(PaymentException)

    if merchant_id is not None:
        query = query.filter(PaymentException.merchant_id == merchant_id)
    if severity is not None:
        query = query.filter(PaymentException.severity == severity)
    if category is not None:
        query = query.filter(PaymentException.category.ilike(f"%{category}%"))
    if status is not None:
        query = query.filter(PaymentException.status == status)
    if assigned_to is not None:
        query = query.filter(PaymentException.assigned_to == assigned_to)
    if date_from is not None:
        query = query.filter(PaymentException.created_at >= date_from)
    if date_to is not None:
        query = query.filter(PaymentException.created_at <= date_to)

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                PaymentException.title.ilike(search_term),
                PaymentException.description.ilike(search_term),
                PaymentException.category.ilike(search_term),
            )
        )

    total = query.count()
    items = (
        query.order_by(PaymentException.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total


def update_exception(
    db: Session,
    exception_id: uuid.UUID,
    payload: ExceptionUpdate,
    current_user: Optional[User] = None,
) -> Optional[PaymentException]:
    """Legacy update method preserved for backward compatibility."""
    exc = get_exception(db, exception_id)
    if not exc:
        return None

    updates = payload.model_dump(exclude_unset=True)
    if updates.get("status") == ExceptionStatus.resolved and exc.status != ExceptionStatus.resolved:
        updates["resolved_at"] = datetime.now(timezone.utc)
        if current_user:
            updates["resolved_by"] = current_user.id

    for field, value in updates.items():
        setattr(exc, field, value)

    exc.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(exc)
    return exc


def assign_exception(
    db: Session,
    exception_id: uuid.UUID,
    user_id: Optional[uuid.UUID],
    current_user: User,
) -> PaymentException:
    """Assign or unassign an exception ticket to a finance operator."""
    exc = get_exception(db, exception_id)
    if not exc:
        raise ValueError("Exception not found")

    if exc.status in (ExceptionStatus.resolved, ExceptionStatus.ignored):
        raise ValueError("Cannot reassign a resolved or ignored exception without reopening it first")

    # If user_id provided, verify assignee exists and is active
    target_user_name = None
    if user_id is not None:
        assignee = db.get(User, user_id)
        if not assignee or not assignee.is_active:
            raise ValueError("Target user for assignment does not exist or is inactive")
        target_user_name = assignee.name

    exc.assigned_to = user_id
    exc.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(exc)

    create_audit_log(
        db,
        action="exception_assigned",
        user_id=current_user.id,
        entity_type="exception",
        entity_id=str(exc.id),
        details={
            "assigned_to": str(user_id) if user_id else None,
            "assignee_name": target_user_name or "Unassigned",
            "assigned_by": current_user.email,
        },
    )

    logger.info("Exception %s assigned to %s by %s", exc.id, user_id, current_user.email)
    return exc


def update_status(
    db: Session,
    exception_id: uuid.UUID,
    new_status: ExceptionStatus,
    current_user: User,
) -> PaymentException:
    """
    Validate and execute status transitions for exception workflow.
    Valid transitions:
      OPEN -> INVESTIGATING
      INVESTIGATING -> INVESTIGATING
    Resolving and Ignoring must go through resolve_exception and ignore_exception.
    """
    exc = get_exception(db, exception_id)
    if not exc:
        raise ValueError("Exception not found")

    if exc.status == new_status:
        return exc

    # Terminal state protection
    if exc.status in (ExceptionStatus.resolved, ExceptionStatus.ignored):
        raise ValueError("Resolved or ignored exceptions cannot be modified without reopening first")

    # Enforce workflow rules
    if exc.status == ExceptionStatus.open:
        if new_status != ExceptionStatus.investigating:
            raise ValueError(f"Open exceptions must move to 'investigating' before '{new_status.value}'")
    elif exc.status == ExceptionStatus.investigating:
        if new_status in (ExceptionStatus.resolved, ExceptionStatus.ignored):
            raise ValueError(f"Use the specific resolve or ignore endpoint to provide mandatory documentation")

    old_status = exc.status
    exc.status = new_status
    exc.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(exc)

    create_audit_log(
        db,
        action="exception_status_changed",
        user_id=current_user.id,
        entity_type="exception",
        entity_id=str(exc.id),
        details={
            "old_status": old_status.value,
            "new_status": new_status.value,
            "updated_by": current_user.email,
        },
    )

    logger.info("Exception %s transitioned %s -> %s", exc.id, old_status.value, new_status.value)
    return exc


def add_review_note(
    db: Session,
    exception_id: uuid.UUID,
    note: str,
    current_user: User,
) -> PaymentException:
    """Record investigation review note and transition from open to investigating."""
    clean_note = _sanitize_string(note)
    if not clean_note:
        raise ValueError("Review note cannot be empty")

    exc = get_exception(db, exception_id)
    if not exc:
        raise ValueError("Exception not found")

    if exc.status in (ExceptionStatus.resolved, ExceptionStatus.ignored):
        raise ValueError("Cannot add notes to a resolved or ignored exception without reopening first")

    # Auto-transition open -> investigating when a human starts reviewing
    if exc.status == ExceptionStatus.open:
        exc.status = ExceptionStatus.investigating

    timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp_str} - {current_user.name}]: {clean_note}"

    if exc.reviewer_note:
        exc.reviewer_note = f"{exc.reviewer_note}\n\n{entry}"
    else:
        exc.reviewer_note = entry

    exc.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(exc)

    create_audit_log(
        db,
        action="exception_reviewed",
        user_id=current_user.id,
        entity_type="exception",
        entity_id=str(exc.id),
        details={
            "note": clean_note,
            "status": exc.status.value,
            "reviewed_by": current_user.email,
        },
    )

    logger.info("Review note added to exception %s by %s", exc.id, current_user.email)
    return exc


def resolve_exception(
    db: Session,
    exception_id: uuid.UUID,
    resolution_note: str,
    current_user: User,
) -> PaymentException:
    """
    Mark an exception as resolved with mandatory human resolution rationale.
    In accordance with core principles, this updates the ticket workflow status
    without modifying underlying financial transactions or ledgers.
    """
    clean_note = _sanitize_string(resolution_note)
    if not clean_note:
        raise ValueError("Resolution note is required and cannot be empty")

    exc = get_exception(db, exception_id)
    if not exc:
        raise ValueError("Exception not found")

    if exc.status == ExceptionStatus.resolved:
        raise ValueError("This exception has already been resolved")

    exc.status = ExceptionStatus.resolved
    exc.resolution_note = clean_note
    exc.resolved_by = current_user.id
    exc.resolved_at = datetime.now(timezone.utc)
    exc.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(exc)

    create_audit_log(
        db,
        action="exception_resolved",
        user_id=current_user.id,
        entity_type="exception",
        entity_id=str(exc.id),
        details={
            "resolution_note": clean_note,
            "resolved_by": current_user.email,
            "resolved_at": exc.resolved_at.isoformat(),
        },
    )

    logger.info("Exception %s resolved by %s", exc.id, current_user.email)
    return exc


def ignore_exception(
    db: Session,
    exception_id: uuid.UUID,
    reason: str,
    current_user: User,
) -> PaymentException:
    """
    Mark an exception as ignored with mandatory reason.
    Used when a discrepancy is known test data or an accepted variance.
    """
    clean_reason = _sanitize_string(reason)
    if not clean_reason:
        raise ValueError("Reason for ignoring exception is required and cannot be empty")

    exc = get_exception(db, exception_id)
    if not exc:
        raise ValueError("Exception not found")

    if exc.status == ExceptionStatus.resolved:
        raise ValueError("Cannot ignore an exception that is already resolved")
    if exc.status == ExceptionStatus.ignored:
        raise ValueError("This exception has already been ignored")

    exc.status = ExceptionStatus.ignored
    exc.resolution_note = f"[IGNORED] {clean_reason}"
    exc.ignored_by = current_user.id
    exc.ignored_at = datetime.now(timezone.utc)
    exc.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(exc)

    create_audit_log(
        db,
        action="exception_ignored",
        user_id=current_user.id,
        entity_type="exception",
        entity_id=str(exc.id),
        details={
            "reason": clean_reason,
            "ignored_by": current_user.email,
            "ignored_at": exc.ignored_at.isoformat(),
        },
    )

    logger.info("Exception %s ignored by %s", exc.id, current_user.email)
    return exc


def escalate_exception(
    db: Session,
    exception_id: uuid.UUID,
    reason: str,
    suggested_team: Optional[str],
    current_user: User,
) -> PaymentException:
    """
    Record an escalation for critical or unresolved discrepancies.
    Creates internal audit and tracking records without external dispatch.
    """
    clean_reason = _sanitize_string(reason)
    if not clean_reason:
        raise ValueError("Escalation reason is required and cannot be empty")

    exc = get_exception(db, exception_id)
    if not exc:
        raise ValueError("Exception not found")

    if exc.status in (ExceptionStatus.resolved, ExceptionStatus.ignored):
        raise ValueError("Cannot escalate a resolved or ignored exception without reopening first")

    exc.escalated_at = datetime.now(timezone.utc)
    exc.escalation_reason = clean_reason
    exc.updated_at = datetime.now(timezone.utc)

    # Auto-ensure status is investigating
    if exc.status == ExceptionStatus.open:
        exc.status = ExceptionStatus.investigating

    db.commit()
    db.refresh(exc)

    create_audit_log(
        db,
        action="exception_escalated",
        user_id=current_user.id,
        entity_type="exception",
        entity_id=str(exc.id),
        details={
            "reason": clean_reason,
            "suggested_team": suggested_team or "Finance Operations",
            "escalated_by": current_user.email,
            "escalated_at": exc.escalated_at.isoformat(),
        },
    )

    logger.info("Exception %s escalated by %s to %s", exc.id, current_user.email, suggested_team)
    return exc


def reopen_exception(
    db: Session,
    exception_id: uuid.UUID,
    reason: Optional[str],
    current_user: User,
) -> PaymentException:
    """Reopen a previously resolved or ignored exception back to investigating."""
    exc = get_exception(db, exception_id)
    if not exc:
        raise ValueError("Exception not found")

    if exc.status not in (ExceptionStatus.resolved, ExceptionStatus.ignored):
        raise ValueError("Only resolved or ignored exceptions can be reopened")

    old_status = exc.status
    exc.status = ExceptionStatus.investigating
    clean_reason = _sanitize_string(reason) or "Reopened for further investigation"

    timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    reopen_note = f"[REOPENED on {timestamp_str} by {current_user.name}]: {clean_reason}"

    if exc.reviewer_note:
        exc.reviewer_note = f"{exc.reviewer_note}\n\n{reopen_note}"
    else:
        exc.reviewer_note = reopen_note

    exc.resolved_at = None
    exc.resolved_by = None
    exc.ignored_at = None
    exc.ignored_by = None
    exc.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(exc)

    create_audit_log(
        db,
        action="exception_reopened",
        user_id=current_user.id,
        entity_type="exception",
        entity_id=str(exc.id),
        details={
            "previous_status": old_status.value,
            "reason": clean_reason,
            "reopened_by": current_user.email,
        },
    )

    logger.info("Exception %s reopened by %s", exc.id, current_user.email)
    return exc


def get_exception_timeline(db: Session, exception_id: uuid.UUID) -> List[TimelineEvent]:
    """
    Construct a complete, strictly grounded chronological timeline of real database events.
    Synthesizes events from:
      1. Exception Creation
      2. Audit Log Records (assignment, status changes, reviews, resolutions, escalations)
      3. AI Analysis execution
      4. Agent Investigation execution
    """
    exc = get_exception(db, exception_id)
    if not exc:
        raise ValueError("Exception not found")

    events: List[TimelineEvent] = []

    # 1. Exception Creation Event
    events.append(
        TimelineEvent(
            id=f"creation_{exc.id}",
            event_type="exception_created",
            title="Exception Ticket Created",
            description=f"Exception logged with severity '{exc.severity.value}' in category '{exc.category or 'General'}'",
            actor="System",
            actor_role="Automated Engine",
            timestamp=exc.created_at,
            metadata={"severity": exc.severity.value, "category": exc.category},
        )
    )

    # 2. Audit Log Events
    audit_logs = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == "exception", AuditLog.entity_id == str(exception_id))
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    ACTION_TITLES = {
        "exception_created": "Exception Initialized",
        "exception_assigned": "Assignee Assigned",
        "exception_status_changed": "Status Updated",
        "exception_reviewed": "Human Review Note Added",
        "exception_resolved": "Exception Resolved",
        "exception_ignored": "Exception Ignored",
        "exception_escalated": "Exception Escalated to Operations",
        "exception_reopened": "Exception Reopened",
    }

    for log in audit_logs:
        # Skip the duplicate creation log since we already appended creation event
        if log.action == "exception_created":
            continue

        actor_name = log.user.name if log.user else "System Operator"
        actor_role = log.user.role.value if log.user else "Operator"

        details = log.details or {}
        desc = ""
        if log.action == "exception_assigned":
            desc = f"Assigned to {details.get('assignee_name', 'operator')}"
        elif log.action == "exception_status_changed":
            desc = f"Workflow status changed from '{details.get('old_status')}' to '{details.get('new_status')}'"
        elif log.action == "exception_reviewed":
            desc = details.get("note", "Review note added")
        elif log.action == "exception_resolved":
            desc = f"Resolution: {details.get('resolution_note', 'Resolved')}"
        elif log.action == "exception_ignored":
            desc = f"Ignored: {details.get('reason', 'Ignored')}"
        elif log.action == "exception_escalated":
            desc = f"Escalated to {details.get('suggested_team')}: {details.get('reason')}"
        elif log.action == "exception_reopened":
            desc = f"Reopened from {details.get('previous_status')}: {details.get('reason')}"

        events.append(
            TimelineEvent(
                id=str(log.id),
                event_type=log.action,
                title=ACTION_TITLES.get(log.action, log.action.replace("_", " ").title()),
                description=desc,
                actor=actor_name,
                actor_role=actor_role,
                timestamp=log.created_at,
                metadata=details,
            )
        )

    # 3. AI Analysis Event (if linked)
    ai_analyses = (
        db.query(AIAnalysis)
        .filter(or_(AIAnalysis.exception_id == exception_id, AIAnalysis.reconciliation_id == exc.reconciliation_id))
        .all()
    )
    for ai in ai_analyses:
        events.append(
            TimelineEvent(
                id=f"ai_{ai.id}",
                event_type="ai_analysis_completed",
                title="AI Mismatch Analysis Completed",
                description=ai.summary or "Root-cause diagnostics evaluated.",
                actor=f"{ai.ai_provider} ({ai.model_name})",
                actor_role="AI Diagnostic Agent",
                timestamp=ai.created_at,
                metadata={
                    "risk_level": ai.risk_level.value,
                    "confidence": float(ai.confidence_score or 0),
                    "recommended_action": ai.recommended_action,
                },
            )
        )

    # 4. Agent Investigation Event (if linked)
    agent_invs = (
        db.query(AgentInvestigation)
        .filter(or_(AgentInvestigation.exception_id == exception_id, AgentInvestigation.reconciliation_id == exc.reconciliation_id))
        .all()
    )
    for inv in agent_invs:
        events.append(
            TimelineEvent(
                id=f"agent_{inv.id}",
                event_type="agent_investigation_completed",
                title=f"AI Agent Triage: {inv.decision.value.upper()}",
                description=inv.summary or "Multi-ledger evidence collected.",
                actor="Autonomous Agent",
                actor_role="Triage Agent",
                timestamp=inv.completed_at or inv.started_at,
                metadata={
                    "decision": inv.decision.value,
                    "confidence": float(inv.confidence_score or 0),
                    "escalation_required": inv.escalation_required,
                    "team": inv.escalation_team,
                },
            )
        )

    # Sort all events chronologically
    events.sort(key=lambda e: e.timestamp)
    return events


def get_exception_details(db: Session, exception_id: uuid.UUID) -> ExceptionDetailedResponse:
    """Load composite graph of exception, transaction, bank statement, recon, AI, and Agent data."""
    exc = get_exception(db, exception_id)
    if not exc:
        raise ValueError("Exception not found")

    recon = exc.reconciliation_result
    txn = recon.transaction if recon else None
    bank_txn = recon.bank_transaction if recon else None

    # Find latest AI Analysis
    ai_record = (
        db.query(AIAnalysis)
        .filter(or_(AIAnalysis.exception_id == exception_id, AIAnalysis.reconciliation_id == exc.reconciliation_id))
        .order_by(AIAnalysis.created_at.desc())
        .first()
    )

    # Find latest Agent Investigation
    inv_record = (
        db.query(AgentInvestigation)
        .filter(or_(AgentInvestigation.exception_id == exception_id, AgentInvestigation.reconciliation_id == exc.reconciliation_id))
        .order_by(AgentInvestigation.created_at.desc())
        .first()
    )

    txn_dict = None
    if txn:
        txn_dict = {
            "id": str(txn.id),
            "reference_id": txn.transaction_reference,
            "order_id": getattr(txn, "order_id", None) or txn.transaction_reference,
            "amount": float(txn.amount),
            "fee_amount": float(getattr(txn, "fee_amount", 0) or 0),
            "currency": txn.currency,
            "gateway": txn.gateway,
            "source": txn.source.value if hasattr(txn.source, "value") else str(txn.source),
            "status": txn.status.value if hasattr(txn.status, "value") else str(txn.status),
            "payment_method": txn.payment_method,
            "created_at": txn.created_at.isoformat(),
        }

    bank_dict = None
    if bank_txn:
        bank_dict = {
            "id": str(bank_txn.id),
            "bank_reference": bank_txn.bank_reference,
            "amount": float(bank_txn.amount),
            "currency": getattr(bank_txn, "currency", "INR") or "INR",
            "bank": bank_txn.bank_name,
            "account_number": getattr(bank_txn, "account_number", None),
            "status": bank_txn.status.value if hasattr(bank_txn.status, "value") else str(bank_txn.status),
            "transaction_date": bank_txn.transaction_date.isoformat() if bank_txn.transaction_date else None,
        }

    recon_dict = None
    if recon:
        recon_dict = {
            "id": str(recon.id),
            "match_status": recon.match_status.value if hasattr(recon.match_status, "value") else str(recon.match_status),
            "expected_amount": float(recon.expected_amount) if recon.expected_amount is not None else None,
            "actual_amount": float(recon.actual_amount) if recon.actual_amount is not None else None,
            "difference_amount": float(recon.difference_amount) if recon.difference_amount is not None else None,
            "confidence_score": float(recon.confidence_score) if recon.confidence_score is not None else None,
            "matching_method": recon.matching_method,
            "explanation": recon.explanation,
            "reconciled_at": recon.reconciled_at.isoformat() if recon.reconciled_at else None,
        }

    ai_dict = None
    if ai_record:
        ai_dict = {
            "id": str(ai_record.id),
            "summary": ai_record.summary,
            "root_cause": ai_record.root_cause,
            "impact": ai_record.impact,
            "recommended_action": ai_record.recommended_action,
            "risk_level": ai_record.risk_level.value,
            "confidence_score": float(ai_record.confidence_score or 0),
            "provider": ai_record.ai_provider,
            "status": ai_record.status.value,
            "created_at": ai_record.created_at.isoformat(),
        }

    inv_dict = None
    if inv_record:
        inv_dict = {
            "id": str(inv_record.id),
            "summary": inv_record.summary,
            "decision": inv_record.decision.value,
            "risk_level": inv_record.risk_level.value,
            "confidence_score": float(inv_record.confidence_score or 0),
            "confirmed_facts": inv_record.confirmed_facts or [],
            "possible_causes": inv_record.possible_causes or [],
            "root_cause": inv_record.root_cause,
            "evidence": inv_record.evidence or [],
            "escalation_required": inv_record.escalation_required,
            "escalation_team": inv_record.escalation_team,
            "recommended_action": inv_record.recommended_action,
            "status": inv_record.status.value,
            "created_at": inv_record.created_at.isoformat(),
        }

    assignee_dict = None
    if exc.assignee:
        assignee_dict = {
            "id": str(exc.assignee.id),
            "name": exc.assignee.name,
            "email": exc.assignee.email,
            "role": exc.assignee.role.value,
        }

    return ExceptionDetailedResponse(
        exception=_enrich_exception_response(exc),
        transaction=txn_dict,
        bank_transaction=bank_dict,
        reconciliation=recon_dict,
        ai_analysis=ai_dict,
        agent_investigation=inv_dict,
        assignee=assignee_dict,
    )


def get_workflow_summary(db: Session, merchant_id: Optional[uuid.UUID] = None) -> ExceptionWorkflowSummary:
    """Compute aggregate exception metrics for the Operations Control Center."""
    base_query = db.query(PaymentException)
    if merchant_id:
        base_query = base_query.filter(PaymentException.merchant_id == merchant_id)

    total_count = base_query.count()
    open_count = base_query.filter(PaymentException.status == ExceptionStatus.open).count()
    investigating_count = base_query.filter(PaymentException.status == ExceptionStatus.investigating).count()
    resolved_count = base_query.filter(PaymentException.status == ExceptionStatus.resolved).count()
    ignored_count = base_query.filter(PaymentException.status == ExceptionStatus.ignored).count()
    critical_count = base_query.filter(PaymentException.severity == ExceptionSeverity.critical).count()
    unassigned_count = (
        base_query.filter(
            PaymentException.assigned_to.is_(None),
            PaymentException.status.in_([ExceptionStatus.open, ExceptionStatus.investigating]),
        ).count()
    )

    # Resolved today
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    resolved_today_count = (
        base_query.filter(
            PaymentException.status == ExceptionStatus.resolved,
            PaymentException.resolved_at >= today_start,
        ).count()
    )

    # Escalated count
    escalated_count = base_query.filter(PaymentException.escalated_at.isnot(None)).count()

    return ExceptionWorkflowSummary(
        total=total_count,
        open=open_count,
        investigating=investigating_count,
        resolved=resolved_count,
        ignored=ignored_count,
        critical=critical_count,
        unassigned=unassigned_count,
        resolved_today=resolved_today_count,
        escalated=escalated_count,
    )
