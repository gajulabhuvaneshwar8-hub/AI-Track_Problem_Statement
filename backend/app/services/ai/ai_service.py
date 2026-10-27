"""
app/services/ai/ai_service.py

High-level facade for all AI analysis operations.
Orchestrates exception analysis, deep investigations, history retrieval,
and duplicate prevention.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis
from app.models.enums import AnalysisStatus, AnalysisType, RiskLevel
from app.models.exception import PaymentException
from app.models.reconciliation_result import ReconciliationResult
from app.schemas.ai_analysis import AIAnalysisResponse, AIInvestigationResponse
from app.services.ai.ai_client import AIClient
from app.services.ai.exception_analyzer import run_analysis

logger = logging.getLogger(__name__)


async def analyze_reconciliation_result(
    db: Session,
    reconciliation_id: uuid.UUID,
    force: bool = False,
    analysis_type: AnalysisType = AnalysisType.exception_analysis,
    ai_client: Optional[AIClient] = None,
) -> AIAnalysis:
    """
    Analyzes a reconciliation result by ID.
    Loads associated transaction and bank transaction records for full context.
    """
    recon = db.get(ReconciliationResult, reconciliation_id)
    if not recon:
        raise ValueError(f"Reconciliation result {reconciliation_id} not found")

    # If an exception exists for this reconciliation, link it as well
    exc = None
    if recon.exceptions:
        exc = recon.exceptions[0]

    return await run_analysis(
        db=db,
        recon=recon,
        exc=exc,
        analysis_type=analysis_type,
        force=force,
        ai_client=ai_client,
    )


async def analyze_exception(
    db: Session,
    exception_id: uuid.UUID,
    force: bool = False,
    analysis_type: AnalysisType = AnalysisType.exception_analysis,
    ai_client: Optional[AIClient] = None,
) -> AIAnalysis:
    """
    Analyzes a specific exception ticket by ID.
    """
    exc = db.get(PaymentException, exception_id)
    if not exc:
        raise ValueError(f"Payment exception {exception_id} not found")

    recon = exc.reconciliation_result

    return await run_analysis(
        db=db,
        recon=recon,
        exc=exc,
        analysis_type=analysis_type,
        force=force,
        ai_client=ai_client,
    )


async def investigate_exception(
    db: Session,
    exception_id: uuid.UUID,
    force: bool = False,
    ai_client: Optional[AIClient] = None,
) -> AIInvestigationResponse:
    """
    Performs a deeper diagnostic investigation of an exception ticket.
    """
    analysis = await analyze_exception(
        db=db,
        exception_id=exception_id,
        force=force,
        analysis_type=AnalysisType.investigation,
        ai_client=ai_client,
    )

    # Build investigation diagnostics
    factors = [
        f"Assessed Risk: {analysis.risk_level.value.upper()}",
        f"Identified Cause: {analysis.root_cause or 'Unspecified variance'}",
        f"Execution Mode: {analysis.status.value.upper()} (Provider: {analysis.ai_provider})",
    ]

    steps = [
        "1. Verify merchant gateway payout settlement file and clearing status.",
        "2. Cross-reference bank statement credit lines within ±2 banking business days.",
        "3. Review chargeback, fee schedule, and reversal queues for deductions.",
        "4. Obtain human controller sign-off prior to closing this ticket.",
    ]

    return AIInvestigationResponse(
        analysis=AIAnalysisResponse.model_validate(analysis),
        investigation_depth="comprehensive",
        discrepancy_factors=factors,
        suggested_audit_steps=steps,
        human_action_required=True,
    )


def list_analyses(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    analysis_type: Optional[AnalysisType] = None,
    risk_level: Optional[RiskLevel] = None,
    status: Optional[AnalysisStatus] = None,
    reconciliation_id: Optional[uuid.UUID] = None,
    exception_id: Optional[uuid.UUID] = None,
) -> Tuple[List[AIAnalysis], int]:
    """
    Returns a paginated list of AI analysis history records.
    """
    stmt = select(AIAnalysis)

    if analysis_type:
        stmt = stmt.where(AIAnalysis.analysis_type == analysis_type)
    if risk_level:
        stmt = stmt.where(AIAnalysis.risk_level == risk_level)
    if status:
        stmt = stmt.where(AIAnalysis.status == status)
    if reconciliation_id:
        stmt = stmt.where(AIAnalysis.reconciliation_id == reconciliation_id)
    if exception_id:
        stmt = stmt.where(AIAnalysis.exception_id == exception_id)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    # Paginated ordered query
    query = stmt.order_by(desc(AIAnalysis.created_at)).offset(skip).limit(limit)
    items = list(db.scalars(query).all())

    return items, total


def get_analysis(db: Session, analysis_id: uuid.UUID) -> Optional[AIAnalysis]:
    """Retrieves a single AI analysis by ID."""
    return db.get(AIAnalysis, analysis_id)


def get_analyses_for_reconciliation(
    db: Session, reconciliation_id: uuid.UUID
) -> List[AIAnalysis]:
    """Returns all historical AI analyses for a reconciliation result."""
    stmt = (
        select(AIAnalysis)
        .where(AIAnalysis.reconciliation_id == reconciliation_id)
        .order_by(desc(AIAnalysis.created_at))
    )
    return list(db.scalars(stmt).all())
