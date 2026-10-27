"""
app/services/ai/exception_analyzer.py

Orchestrates AI analysis for reconciliation results and exceptions.
Builds safe, sanitized financial context, invokes the AI client or fallback analyzer,
and persists an auditable AIAnalysis record in the database.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis
from app.models.enums import AnalysisStatus, AnalysisType
from app.models.exception import PaymentException
from app.models.reconciliation_result import ReconciliationResult
from app.services.ai.ai_client import AIClient, AIAvailabilityError, default_ai_client
from app.services.ai.fallback_analyzer import analyze_fallback
from app.services.ai.prompts import SYSTEM_PROMPT, build_analysis_prompt
from app.services.ai.response_parser import AIResponseParseError, parse_ai_response

logger = logging.getLogger(__name__)


def build_safe_context(
    recon: Optional[ReconciliationResult],
    exc: Optional[PaymentException],
) -> Dict[str, Any]:
    """
    Constructs a strictly sanitized dictionary with only financial audit fields.
    Never includes credentials, tokens, PII, or internal keys.
    """
    context: Dict[str, Any] = {
        "reconciliation": {},
        "exception": {},
        "transaction": {},
        "bank_transaction": {},
    }

    if recon:
        context["reconciliation"] = {
            "reconciliation_id": str(recon.id),
            "match_status": recon.match_status.value if recon.match_status else None,
            "matching_method": recon.matching_method,
            "expected_amount": str(recon.expected_amount) if recon.expected_amount is not None else None,
            "actual_amount": str(recon.actual_amount) if recon.actual_amount is not None else None,
            "difference_amount": str(recon.difference_amount) if recon.difference_amount is not None else None,
            "confidence_score": str(recon.confidence_score) if recon.confidence_score is not None else None,
            "existing_explanation": recon.explanation,
            "reconciled_at": recon.reconciled_at.isoformat() if recon.reconciled_at else None,
        }

        if recon.transaction:
            t = recon.transaction
            context["transaction"] = {
                "transaction_reference": t.transaction_reference,
                "order_reference": t.order_reference,
                "amount": str(t.amount) if t.amount is not None else None,
                "currency": t.currency,
                "transaction_date": t.transaction_date.isoformat() if t.transaction_date else None,
                "payment_method": t.payment_method,
                "gateway": t.gateway,
                "status": t.status.value if t.status else None,
            }

        if recon.bank_transaction:
            b = recon.bank_transaction
            context["bank_transaction"] = {
                "bank_reference": b.bank_reference,
                "transaction_reference": b.transaction_reference,
                "amount": str(b.amount) if b.amount is not None else None,
                "currency": getattr(b, "currency", None) or getattr(recon.transaction, "currency", "INR"),
                "transaction_date": b.transaction_date.isoformat() if b.transaction_date else None,
                "bank_name": b.bank_name,
                "status": b.status if isinstance(b.status, str) else (b.status.value if b.status else None),
            }

    if exc:
        context["exception"] = {
            "exception_id": str(exc.id),
            "severity": exc.severity.value if exc.severity else None,
            "category": exc.category,
            "title": exc.title,
            "description": exc.description,
            "recommended_action": exc.recommended_action,
            "status": exc.status.value if exc.status else None,
            "created_at": exc.created_at.isoformat() if exc.created_at else None,
        }

    return context


async def run_analysis(
    db: Session,
    recon: Optional[ReconciliationResult] = None,
    exc: Optional[PaymentException] = None,
    analysis_type: AnalysisType = AnalysisType.exception_analysis,
    force: bool = False,
    ai_client: Optional[AIClient] = None,
) -> AIAnalysis:
    """
    Main analysis execution flow:
      1. Check existing record unless force=True
      2. Build safe context
      3. Try AI Client
      4. On any failure, execute fallback analyzer
      5. Persist and return AIAnalysis record
    """
    client = ai_client or default_ai_client

    # 1. Check existing unless force=True
    if not force:
        query = select(AIAnalysis).where(AIAnalysis.analysis_type == analysis_type)
        if recon and exc:
            query = query.where(
                (AIAnalysis.reconciliation_id == recon.id) | (AIAnalysis.exception_id == exc.id)
            )
        elif recon:
            query = query.where(AIAnalysis.reconciliation_id == recon.id)
        elif exc:
            query = query.where(AIAnalysis.exception_id == exc.id)

        query = query.order_by(AIAnalysis.created_at.desc())
        existing = db.execute(query).scalars().first()
        if existing:
            logger.info("Returning cached AI analysis %s (force=False)", existing.id)
            return existing

    # 2. Build safe context
    context = build_safe_context(recon, exc)

    logger.info(
        "Starting AI analysis: type=%s recon_id=%s exc_id=%s",
        analysis_type.value,
        recon.id if recon else None,
        exc.id if exc else None,
    )

    parsed_data = None
    raw_response = None
    status = AnalysisStatus.completed
    provider = "gemini"
    model_name = client.model_name

    # 3. Call AI Client
    try:
        prompt = build_analysis_prompt(context, analysis_type.value)
        raw_response = await client.generate_analysis(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        parsed_data = parse_ai_response(raw_response)
        logger.info("AI analysis completed successfully via provider=%s", provider)
    except (AIAvailabilityError, AIResponseParseError, Exception) as exc_err:
        logger.warning(
            "AI provider unavailable or returned invalid output (%s). Running deterministic fallback analyzer.",
            exc_err,
        )
        parsed_data = analyze_fallback(context, analysis_type.value)
        status = AnalysisStatus.fallback
        provider = "fallback"
        model_name = "rule-based-fallback-v1"
        raw_response = parsed_data.get("raw_response")

    # 4. Save to Database
    analysis_record = AIAnalysis(
        id=uuid.uuid4(),
        reconciliation_id=recon.id if recon else None,
        exception_id=exc.id if exc else None,
        analysis_type=analysis_type,
        summary=parsed_data["summary"],
        root_cause=parsed_data.get("root_cause"),
        impact=parsed_data.get("impact"),
        recommended_action=parsed_data.get("recommended_action"),
        risk_level=parsed_data["risk_level"],
        confidence_score=parsed_data.get("confidence_score"),
        ai_provider=provider,
        model_name=model_name,
        status=status,
        raw_response=raw_response,
    )

    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)

    logger.info(
        "AI analysis stored successfully: id=%s status=%s risk=%s",
        analysis_record.id,
        analysis_record.status.value,
        analysis_record.risk_level.value,
    )
    return analysis_record
