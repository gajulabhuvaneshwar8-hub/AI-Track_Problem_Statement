"""
app/api/routes/agents.py

FastAPI endpoints for the AI Reconciliation Investigation Agent (Step 7).
Provides:
  POST /api/agents/investigate/{exception_id}
  POST /api/agents/investigate/reconciliation/{reconciliation_id}
  GET  /api/agents/investigations
  GET  /api/agents/investigations/{investigation_id}
  GET  /api/agents/investigations/{investigation_id}/evidence
  POST /api/agents/investigations/{investigation_id}/escalate
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_user,
    get_db_session,
    require_finance_or_admin,
)
from app.models.agent_investigation import AgentInvestigation
from app.models.enums import AgentDecision, InvestigationStatus, RiskLevel, UserRole
from app.models.user import User
from app.schemas.agent import (
    AgentInvestigationResponse,
    EscalationResponse,
    PaginatedAgentInvestigations,
)
from app.services.agents import investigation_service
from app.services.agents.escalation_service import EscalationService
from app.services.agents.reconciliation_agent import ReconciliationAgent

logger = logging.getLogger("app.api.agents")
router = APIRouter(prefix="/agents", tags=["AI Reconciliation Agent"])


@router.post(
    "/investigate/{exception_id}",
    response_model=AgentInvestigationResponse,
    summary="Start an automated investigation for a reconciliation exception",
    status_code=status.HTTP_200_OK,
)
async def investigate_exception(
    exception_id: uuid.UUID,
    force: bool = Query(
        False,
        description="Force a new investigation even if an investigation is already completed",
    ),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_finance_or_admin),
) -> AgentInvestigationResponse:
    """
    Triggers an autonomous investigation of a reconciliation exception.
    Gathers evidence from ledgers and settlements, runs deterministic decision rules,
    synthesizes insights via AI/fallback, and returns structured findings.
    """
    agent = ReconciliationAgent(db=db)
    try:
        inv = await agent.investigate_exception(
            exception_id=exception_id,
            force=force,
            current_user=current_user,
        )
        return AgentInvestigationResponse.model_validate(inv)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post(
    "/investigate/reconciliation/{reconciliation_id}",
    response_model=AgentInvestigationResponse,
    summary="Start an automated investigation for a reconciliation result directly",
    status_code=status.HTTP_200_OK,
)
async def investigate_reconciliation(
    reconciliation_id: uuid.UUID,
    force: bool = Query(
        False,
        description="Force a new investigation even if already completed",
    ),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_finance_or_admin),
) -> AgentInvestigationResponse:
    """
    Triggers an autonomous investigation of a specific reconciliation match result.
    """
    agent = ReconciliationAgent(db=db)
    try:
        inv = await agent.investigate_reconciliation(
            reconciliation_id=reconciliation_id,
            force=force,
            current_user=current_user,
        )
        return AgentInvestigationResponse.model_validate(inv)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/investigations",
    response_model=PaginatedAgentInvestigations,
    summary="List agent investigations with filtering and pagination",
)
def list_investigations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    exception_id: Optional[uuid.UUID] = Query(None),
    reconciliation_id: Optional[uuid.UUID] = Query(None),
    status: Optional[InvestigationStatus] = Query(None),
    decision: Optional[AgentDecision] = Query(None),
    risk_level: Optional[RiskLevel] = Query(None),
    merchant_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_finance_or_admin),
) -> PaginatedAgentInvestigations:
    """
    Lists investigations. Admins can view all; finance users view their permitted merchant data.
    """
    skip = (page - 1) * page_size
    items, total = investigation_service.list_investigations(
        db=db,
        skip=skip,
        limit=page_size,
        exception_id=exception_id,
        reconciliation_id=reconciliation_id,
        status=status,
        decision=decision,
        risk_level=risk_level,
        merchant_id=merchant_id,
    )
    return PaginatedAgentInvestigations(
        items=[AgentInvestigationResponse.model_validate(i) for i in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/investigations/{investigation_id}",
    response_model=AgentInvestigationResponse,
    summary="Get complete investigation details by ID",
)
def get_investigation(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_finance_or_admin),
) -> AgentInvestigationResponse:
    """
    Returns the complete structured findings of an investigation.
    """
    inv = investigation_service.get_investigation(db, investigation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation {investigation_id} not found",
        )
    return AgentInvestigationResponse.model_validate(inv)


@router.get(
    "/investigations/{investigation_id}/evidence",
    response_model=List[Dict[str, Any]],
    summary="Get empirical evidence items collected for an investigation",
)
def get_investigation_evidence(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_finance_or_admin),
) -> List[Dict[str, Any]]:
    """
    Returns the array of empirical ledger evidence points collected for this investigation.
    """
    inv = investigation_service.get_investigation(db, investigation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation {investigation_id} not found",
        )
    return inv.evidence or []


@router.post(
    "/investigations/{investigation_id}/escalate",
    response_model=EscalationResponse,
    summary="Generate or update escalation recommendation for an investigation",
)
def escalate_investigation(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_finance_or_admin),
) -> EscalationResponse:
    """
    Generates/refreshes an escalation recommendation for an investigation without dispatching external messages.
    """
    inv = investigation_service.get_investigation(db, investigation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation {investigation_id} not found",
        )

    agent = ReconciliationAgent(db=db)
    context = agent.collect_evidence(
        exception_id=inv.exception_id,
        reconciliation_id=inv.reconciliation_id,
    )
    escalation_service = EscalationService()
    recommendation = escalation_service.generate_recommendation(
        context=context,
        decision_rationale=inv.summary,
    )

    inv.escalation_required = True
    inv.escalation_team = recommendation.recommended_team
    db.commit()
    db.refresh(inv)

    return escalation_service.to_schema(recommendation)
