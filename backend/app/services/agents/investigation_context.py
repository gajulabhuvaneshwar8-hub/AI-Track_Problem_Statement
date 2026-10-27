"""
app/services/agents/investigation_context.py

InvestigationContext data carrier for the AI Reconciliation Investigation Agent.
Contains all verified facts, ledger records, settlements, and related history
collected during an investigation.

CRITICAL SECURITY REQUIREMENT:
The context must contain only information necessary for investigation.
Do NOT expose:
  - passwords
  - JWT secrets
  - API keys
  - credentials
  - internal security secrets
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.ai_analysis import AIAnalysis
from app.models.bank_transaction import BankTransaction
from app.models.exception import PaymentException
from app.models.reconciliation_result import ReconciliationResult
from app.models.settlement import Settlement
from app.models.transaction import Transaction


@dataclass
class InvestigationContext:
    """
    Sanitized context holding all financial artifacts gathered for an exception investigation.
    """

    reconciliation_result: Optional[ReconciliationResult] = None
    transaction: Optional[Transaction] = None
    bank_transaction: Optional[BankTransaction] = None
    settlement: Optional[Settlement] = None
    exception: Optional[PaymentException] = None
    related_transactions: List[Transaction] = field(default_factory=list)
    related_exceptions: List[PaymentException] = field(default_factory=list)
    previous_ai_analyses: List[AIAnalysis] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    investigation_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_safe_dict(self) -> Dict[str, Any]:
        """
        Exports a clean, structured dictionary safe for AI prompts and audit logs.
        Never includes password hashes, API keys, or JWT tokens.
        """
        t = self.transaction
        b = self.bank_transaction
        r = self.reconciliation_result
        s = self.settlement
        e = self.exception

        return {
            "investigation_timestamp": self.investigation_timestamp.isoformat(),
            "transaction": {
                "id": str(t.id) if t else None,
                "reference": t.transaction_reference if t else None,
                "order_reference": t.order_reference if t else None,
                "amount": str(t.amount) if t and t.amount is not None else None,
                "currency": t.currency if t else None,
                "date": t.transaction_date.isoformat() if t and t.transaction_date else None,
                "status": t.status.value if t and t.status else None,
                "gateway": t.gateway if t else None,
                "payment_method": t.payment_method if t else None,
                "merchant_id": str(t.merchant_id) if t and t.merchant_id else None,
            } if t else None,
            "bank_transaction": {
                "id": str(b.id) if b else None,
                "bank_reference": b.bank_reference if b else None,
                "transaction_reference": b.transaction_reference if b else None,
                "amount": str(b.amount) if b and b.amount is not None else None,
                "date": b.transaction_date.isoformat() if b and b.transaction_date else None,
                "status": b.status.value if (b and hasattr(b.status, "value")) else (b.status if b else None),
                "bank_name": b.bank_name if b else None,
            } if b else None,
            "reconciliation": {
                "id": str(r.id) if r else None,
                "match_status": r.match_status.value if r and r.match_status else None,
                "expected_amount": str(r.expected_amount) if r and r.expected_amount is not None else None,
                "actual_amount": str(r.actual_amount) if r and r.actual_amount is not None else None,
                "difference_amount": str(r.difference_amount) if r and r.difference_amount is not None else None,
                "matching_method": r.matching_method if r else None,
                "confidence_score": str(r.confidence_score) if r and r.confidence_score is not None else None,
            } if r else None,
            "settlement": {
                "id": str(s.id) if s else None,
                "settlement_reference": s.settlement_reference if s else None,
                "settlement_date": s.settlement_date.isoformat() if s and s.settlement_date else None,
                "gross_amount": str(s.gross_amount) if s and s.gross_amount is not None else None,
                "fees": str(s.fees) if s and s.fees is not None else None,
                "taxes": str(s.taxes) if s and s.taxes is not None else None,
                "refunds": str(s.refunds) if s and s.refunds is not None else None,
                "chargebacks": str(s.chargebacks) if s and s.chargebacks is not None else None,
                "net_amount": str(s.net_amount) if s and s.net_amount is not None else None,
                "status": s.status.value if s and s.status else None,
            } if s else None,
            "exception": {
                "id": str(e.id) if e else None,
                "severity": e.severity.value if e and e.severity else None,
                "category": e.category if e else None,
                "title": e.title if e else None,
                "description": e.description if e else None,
                "status": e.status.value if e and e.status else None,
            } if e else None,
            "related_history": {
                "similar_transaction_count": len(self.related_transactions),
                "prior_exception_count": len(self.related_exceptions),
                "prior_ai_analyses_count": len(self.previous_ai_analyses),
            },
            "evidence_count": len(self.evidence),
        }
