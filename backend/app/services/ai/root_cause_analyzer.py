"""
app/services/ai/root_cause_analyzer.py

Specialized analyzer focused on identifying root causes for reconciliation anomalies.
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


async def analyze_root_cause(
    db: Session,
    recon: Optional[ReconciliationResult] = None,
    exc: Optional[PaymentException] = None,
    force: bool = False,
    ai_client: Optional[AIClient] = None,
) -> AIAnalysis:
    """
    Executes a targeted root-cause analysis for the provided reconciliation or exception.
    """
    return await run_analysis(
        db=db,
        recon=recon,
        exc=exc,
        analysis_type=AnalysisType.root_cause,
        force=force,
        ai_client=ai_client,
    )
