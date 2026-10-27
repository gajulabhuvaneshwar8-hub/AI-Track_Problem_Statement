"""
app/api/routes/exceptions.py

Comprehensive Exception Management & Human-in-the-Loop workflow API endpoints.
Provides complete lifecycle management: assignment, state transitions, review notes,
grounded resolution/ignoring, internal escalation, reopening, timeline aggregation,
and deep details inspection.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db_session
from app.models.enums import ExceptionSeverity, ExceptionStatus
from app.models.user import User
from app.schemas.exception import (
    ExceptionAssignRequest,
    ExceptionCreate,
    ExceptionDetailedResponse,
    ExceptionEscalateRequest,
    ExceptionIgnoreRequest,
    ExceptionReopenRequest,
    ExceptionResolveRequest,
    ExceptionResponse,
    ExceptionReviewRequest,
    ExceptionStatusRequest,
    ExceptionTimelineResponse,
    ExceptionUpdate,
    ExceptionWorkflowSummary,
    PaginatedExceptions,
)
from app.schemas.user import UserResponse
from app.services import exception_service, user_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/exceptions", tags=["Exceptions"])


# ---------------------------------------------------------------------------
# Global & Collection Endpoints (defined before path parameters)
# ---------------------------------------------------------------------------


@router.get(
    "/workflow-summary",
    response_model=ExceptionWorkflowSummary,
    summary="Get aggregated exception workflow status summary",
)
def get_workflow_summary(
    merchant_id: Optional[uuid.UUID] = Query(None, description="Optional filter by merchant"),
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> ExceptionWorkflowSummary:
    return exception_service.get_workflow_summary(db, merchant_id=merchant_id)


@router.get(
    "/assignees",
    response_model=List[UserResponse],
    summary="List active team members assignable to exceptions",
)
def list_assignees(
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> List[UserResponse]:
    users = user_service.list_assignable_users(db)
    return [UserResponse.model_validate(u) for u in users]


@router.post(
    "",
    response_model=ExceptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a reconciliation exception",
)
def create_exception(
    payload: ExceptionCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExceptionResponse:
    try:
        exc = exception_service.create_exception(db, payload, current_user=current_user)
        return exception_service._enrich_exception_response(exc)
    except Exception as e:
        logger.error("Failed to create exception: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=PaginatedExceptions,
    summary="List exceptions with optional filters and full-text search",
)
def list_exceptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[ExceptionSeverity] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[ExceptionStatus] = Query(None),
    assigned_to: Optional[uuid.UUID] = Query(None),
    merchant_id: Optional[uuid.UUID] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> PaginatedExceptions:
    skip = (page - 1) * page_size
    items, total = exception_service.list_exceptions(
        db,
        severity=severity,
        category=category,
        status=status,
        assigned_to=assigned_to,
        merchant_id=merchant_id,
        search=search,
        skip=skip,
        limit=page_size,
    )
    enriched_items = [exception_service._enrich_exception_response(item) for item in items]
    return PaginatedExceptions(items=enriched_items, page=page, page_size=page_size, total=total)


# ---------------------------------------------------------------------------
# Individual Exception Retrieval & Details
# ---------------------------------------------------------------------------


@router.get(
    "/{exception_id}",
    response_model=ExceptionResponse,
    summary="Get a single exception by ID",
)
def get_exception(
    exception_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> ExceptionResponse:
    exc = exception_service.get_exception(db, exception_id)
    if not exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exception not found",
        )
    return exception_service._enrich_exception_response(exc)


@router.get(
    "/{exception_id}/details",
    response_model=ExceptionDetailedResponse,
    summary="Get detailed exception context including transaction, bank evidence, AI analysis, and investigation",
)
def get_exception_details(
    exception_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> ExceptionDetailedResponse:
    details = exception_service.get_exception_details(db, exception_id)
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exception not found",
        )
    return details


@router.get(
    "/{exception_id}/timeline",
    response_model=ExceptionTimelineResponse,
    summary="Get grounded audit and event timeline for an exception",
)
def get_exception_timeline(
    exception_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> ExceptionTimelineResponse:
    try:
        events = exception_service.get_exception_timeline(db, exception_id)
        return ExceptionTimelineResponse(exception_id=exception_id, events=events)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/{exception_id}",
    response_model=ExceptionResponse,
    summary="Update an exception directly",
)
def update_exception(
    exception_id: uuid.UUID,
    payload: ExceptionUpdate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExceptionResponse:
    try:
        exc = exception_service.update_exception(
            db, exception_id, payload, current_user=current_user
        )
        if not exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exception not found")
        return exception_service._enrich_exception_response(exc)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# Human-in-the-Loop Workflow Transition Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{exception_id}/assign",
    response_model=ExceptionResponse,
    summary="Assign or reassign an exception to an analyst",
)
def assign_exception(
    exception_id: uuid.UUID,
    payload: ExceptionAssignRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExceptionResponse:
    try:
        exc = exception_service.assign_exception(
            db,
            exception_id=exception_id,
            user_id=payload.assigned_to,
            current_user=current_user,
        )
        return exception_service._enrich_exception_response(exc)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{exception_id}/status",
    response_model=ExceptionResponse,
    summary="Transition exception workflow status",
)
def update_status(
    exception_id: uuid.UUID,
    payload: ExceptionStatusRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExceptionResponse:
    try:
        exc = exception_service.update_status(
            db,
            exception_id=exception_id,
            new_status=payload.status,
            current_user=current_user,
        )
        if payload.note:
            exc = exception_service.add_review_note(
                db,
                exception_id=exception_id,
                note=payload.note,
                current_user=current_user,
            )
        return exception_service._enrich_exception_response(exc)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{exception_id}/review",
    response_model=ExceptionResponse,
    summary="Add human review / investigation notes",
)
def add_review_note(
    exception_id: uuid.UUID,
    payload: ExceptionReviewRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExceptionResponse:
    try:
        exc = exception_service.add_review_note(
            db,
            exception_id=exception_id,
            note=payload.note,
            current_user=current_user,
        )
        return exception_service._enrich_exception_response(exc)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{exception_id}/resolve",
    response_model=ExceptionResponse,
    summary="Resolve an exception with mandatory resolution notes",
)
def resolve_exception(
    exception_id: uuid.UUID,
    payload: ExceptionResolveRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExceptionResponse:
    try:
        exc = exception_service.resolve_exception(
            db,
            exception_id=exception_id,
            resolution_note=payload.resolution_note,
            current_user=current_user,
        )
        return exception_service._enrich_exception_response(exc)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{exception_id}/ignore",
    response_model=ExceptionResponse,
    summary="Mark an exception as ignored with mandatory reason",
)
def ignore_exception(
    exception_id: uuid.UUID,
    payload: ExceptionIgnoreRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExceptionResponse:
    try:
        exc = exception_service.ignore_exception(
            db,
            exception_id=exception_id,
            reason=payload.reason,
            current_user=current_user,
        )
        return exception_service._enrich_exception_response(exc)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{exception_id}/escalate",
    response_model=ExceptionResponse,
    summary="Escalate an exception internally with mandatory reason",
)
def escalate_exception(
    exception_id: uuid.UUID,
    payload: ExceptionEscalateRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExceptionResponse:
    try:
        exc = exception_service.escalate_exception(
            db,
            exception_id=exception_id,
            reason=payload.reason,
            suggested_team=payload.suggested_team,
            current_user=current_user,
        )
        return exception_service._enrich_exception_response(exc)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/{exception_id}/reopen",
    response_model=ExceptionResponse,
    summary="Reopen a resolved or ignored exception with audit explanation",
)
def reopen_exception(
    exception_id: uuid.UUID,
    payload: ExceptionReopenRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ExceptionResponse:
    try:
        exc = exception_service.reopen_exception(
            db,
            exception_id=exception_id,
            reason=payload.reason,
            current_user=current_user,
        )
        return exception_service._enrich_exception_response(exc)
    except LookupError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
