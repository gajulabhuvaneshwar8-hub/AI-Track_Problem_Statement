"""
app/services/ai/recommendation_service.py

Produces actionable next steps, remediation actions, and operational guidance
for finance controllers and operations teams.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis
from app.models.enums import AnalysisType
from app.models.exception import PaymentException
from app.models.reconciliation_result import ReconciliationResult
from app.services.ai.ai_client import AIClient
from app.services.ai.exception_analyzer import run_analysis

logger = logging.getLogger(__name__)


async def generate_recommendations(
    db: Session,
    recon: Optional[ReconciliationResult] = None,
    exc: Optional[PaymentException] = None,
    force: bool = False,
    ai_client: Optional[AIClient] = None,
) -> AIAnalysis:
    """
    Produces actionable next steps for resolving a discrepancy without auto-modifying financial records.
    """
    return await run_analysis(
        db=db,
        recon=recon,
        exc=exc,
        analysis_type=AnalysisType.recommendation,
        force=force,
        ai_client=ai_client,
    )
