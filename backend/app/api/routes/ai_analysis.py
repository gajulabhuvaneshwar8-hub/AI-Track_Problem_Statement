"""
app/api/routes/ai_analysis.py

FastAPI router for AI-powered exception analysis, root causes, recommendations,
and investigations.
Enforces authentication and authorization (Finance controllers and Admins).
Never allows AI to modify underlying financial records or statuses.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db_session, require_finance_or_admin
from app.models.enums import AnalysisStatus, AnalysisType, RiskLevel
from app.models.user import User
from app.schemas.ai_analysis import (
    AIAnalysisListResponse,
    AIAnalysisResponse,
    AIInvestigationResponse,
)
from app.services.ai import ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Analysis"])


@router.post(
    "/analyze/{reconciliation_id}",
    response_model=AIAnalysisResponse,
    summary="Analyze a reconciliation result with AI",
    status_code=status.HTTP_200_OK,
)
async def analyze_reconciliation(
    reconciliation_id: uuid.UUID,
    force: bool = Query(
        False, description="Force a new analysis even if a previous one exists"
    ),
    analysis_type: AnalysisType = Query(
        AnalysisType.exception_analysis, description="Analysis variant"
    ),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_finance_or_admin),
) -> AIAnalysisResponse:
    """
    Executes an AI analysis (or deterministic fallback) for a reconciliation result.
    Does not modify financial transaction amounts or matching decisions.
    """
    try:
        analysis = await ai_service.analyze_reconciliation_result(
            db=db,
            reconciliation_id=reconciliation_id,
            force=force,
            analysis_type=analysis_type,
        )
        return AIAnalysisResponse.model_validate(analysis)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post(
    "/analyze/exception/{exception_id}",
    response_model=AIAnalysisResponse,
    summary="Analyze a specific exception ticket with AI",
    status_code=status.HTTP_200_OK,
)
async def analyze_exception_ticket(
    exception_id: uuid.UUID,
    force: bool = Query(
        False, description="Force a new analysis even if a previous one exists"
    ),
    analysis_type: AnalysisType = Query(
        AnalysisType.exception_analysis, description="Analysis variant"
    ),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_finance_or_admin),
) -> AIAnalysisResponse:
    """
    Executes an AI analysis (or deterministic fallback) for an exception ticket.
    """
    try:
        analysis = await ai_service.analyze_exception(
            db=db,
            exception_id=exception_id,
            force=force,
            analysis_type=analysis_type,
        )
        return AIAnalysisResponse.model_validate(analysis)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.post(
    "/investigate/{exception_id}",
    response_model=AIInvestigationResponse,
    summary="Perform an in-depth diagnostic investigation of an exception",
    status_code=status.HTTP_200_OK,
)
async def investigate_exception_endpoint(
    exception_id: uuid.UUID,
    force: bool = Query(False, description="Force fresh re-investigation"),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_finance_or_admin),
) -> AIInvestigationResponse:
    """
    Deep-dive investigation producing audit factors and controller action checklists.
    """
    try:
        return await ai_service.investigate_exception(
            db=db,
            exception_id=exception_id,
            force=force,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get(
    "/analyses",
    response_model=AIAnalysisListResponse,
    summary="List historical AI analyses with filters",
)
def list_ai_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    analysis_type: Optional[AnalysisType] = Query(None),
    risk_level: Optional[RiskLevel] = Query(None),
    status_filter: Optional[AnalysisStatus] = Query(None, alias="status"),
    reconciliation_id: Optional[uuid.UUID] = Query(None),
    exception_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db_session),
    _: User = Depends(require_finance_or_admin),
) -> AIAnalysisListResponse:
    """
    Returns paginated AI analysis history. Preserves complete historical audit trail.
    """
    skip = (page - 1) * page_size
    items, total = ai_service.list_analyses(
        db=db,
        skip=skip,
        limit=page_size,
        analysis_type=analysis_type,
        risk_level=risk_level,
        status=status_filter,
        reconciliation_id=reconciliation_id,
        exception_id=exception_id,
    )
    return AIAnalysisListResponse(
        items=[AIAnalysisResponse.model_validate(x) for x in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/analyses/{analysis_id}",
    response_model=AIAnalysisResponse,
    summary="Retrieve a specific AI analysis by ID",
)
def get_ai_analysis(
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_finance_or_admin),
) -> AIAnalysisResponse:
    """
    Fetches an individual analysis record by its unique ID.
    """
    analysis = ai_service.get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with ID {analysis_id} not found",
        )
    return AIAnalysisResponse.model_validate(analysis)


@router.get(
    "/analyses/reconciliation/{reconciliation_id}",
    response_model=List[AIAnalysisResponse],
    summary="Get all AI analyses for a reconciliation result",
)
def get_analyses_for_reconciliation_endpoint(
    reconciliation_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(require_finance_or_admin),
) -> List[AIAnalysisResponse]:
    """
    Returns full history of analyses executed for a specific reconciliation result.
    """
    analyses = ai_service.get_analyses_for_reconciliation(db, reconciliation_id)
    return [AIAnalysisResponse.model_validate(x) for x in analyses]
