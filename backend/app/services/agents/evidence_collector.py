"""
app/services/agents/evidence_collector.py

EvidenceCollector for the AI Reconciliation Investigation Agent (Step 7).
Gathers verified evidence points across:
  - Gateway Transaction
  - Bank Transaction
  - Reconciliation Result
  - Settlement Batch
  - Exception Ticket
  - Historical Exceptions & Prior AI Analyses

Every evidence item conforms to:
{
    "source": "...",
    "field": "...",
    "value": "...",
    "reliability": 0.0 to 1.0
}

Strict rule: Do not allow the AI to invent evidence. Grounded solely in database fields.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.exception import PaymentException
from app.models.reconciliation_result import ReconciliationResult
from app.services.agents import agent_tools
from app.services.agents.investigation_context import InvestigationContext


class EvidenceCollector:
    """
    Collects and validates empirical evidence from ledger systems.
    """

    def __init__(self, db: Session):
        self.db = db

    def collect(
        self,
        exception_id: Optional[uuid.UUID] = None,
        reconciliation_id: Optional[uuid.UUID] = None,
    ) -> InvestigationContext:
        """
        Gathers all related ledger and settlement data into a structured InvestigationContext.
        """
        exc: Optional[PaymentException] = None
        recon: Optional[ReconciliationResult] = None

        if exception_id:
            exc = self.db.get(PaymentException, exception_id)
            if exc and exc.reconciliation_id:
                recon = agent_tools.get_reconciliation_result(self.db, exc.reconciliation_id)
        elif reconciliation_id:
            recon = agent_tools.get_reconciliation_result(self.db, reconciliation_id)
            if recon and recon.exceptions:
                exc = recon.exceptions[0]

        txn = recon.transaction if (recon and recon.transaction) else None
        btxn = recon.bank_transaction if (recon and recon.bank_transaction) else None

        # Settlement batch lookup
        merchant_id = txn.merchant_id if txn else None
        txn_date = txn.transaction_date if txn else (btxn.transaction_date if btxn else None)
        settlement = agent_tools.get_settlement(self.db, merchant_id, txn_date)

        # Related transactions (e.g. duplicate checks)
        txn_ref = txn.transaction_reference if txn else (btxn.transaction_reference if btxn else None)
        order_ref = txn.order_reference if txn else None
        related_txns = agent_tools.get_related_transactions(
            self.db,
            transaction_reference=txn_ref,
            order_reference=order_ref,
            exclude_id=txn.id if txn else None,
        )

        # Related exceptions
        related_exceptions = agent_tools.get_related_exceptions(
            self.db,
            transaction_id=txn.id if txn else None,
            reconciliation_id=recon.id if recon else None,
            exclude_id=exc.id if exc else None,
        )

        # Previous AI analyses
        previous_analyses = agent_tools.get_previous_ai_analyses(
            self.db,
            reconciliation_id=recon.id if recon else None,
            exception_id=exc.id if exc else None,
        )

        # Compile evidence list
        evidence_items: List[Dict[str, Any]] = []

        # 1. Gateway Transaction Evidence
        if txn:
            evidence_items.extend([
                {"source": "gateway", "field": "transaction_reference", "value": txn.transaction_reference, "reliability": 1.0},
                {"source": "gateway", "field": "amount", "value": str(txn.amount), "reliability": 1.0},
                {"source": "gateway", "field": "status", "value": txn.status.value, "reliability": 1.0},
                {"source": "gateway", "field": "gateway_name", "value": txn.gateway, "reliability": 1.0},
                {"source": "gateway", "field": "transaction_date", "value": txn.transaction_date.isoformat(), "reliability": 1.0},
            ])
            if txn.order_reference:
                evidence_items.append(
                    {"source": "gateway", "field": "order_reference", "value": txn.order_reference, "reliability": 1.0}
                )
        else:
            evidence_items.append(
                {"source": "gateway", "field": "record_presence", "value": "MISSING_IN_GATEWAY", "reliability": 1.0}
            )

        # 2. Bank Transaction Evidence
        if btxn:
            evidence_items.extend([
                {"source": "bank", "field": "bank_reference", "value": btxn.bank_reference, "reliability": 1.0},
                {"source": "bank", "field": "transaction_reference", "value": btxn.transaction_reference, "reliability": 1.0},
                {"source": "bank", "field": "amount", "value": str(btxn.amount), "reliability": 1.0},
                {"source": "bank", "field": "status", "value": btxn.status if isinstance(btxn.status, str) else btxn.status.value, "reliability": 1.0},
                {"source": "bank", "field": "bank_name", "value": btxn.bank_name, "reliability": 1.0},
                {"source": "bank", "field": "transaction_date", "value": btxn.transaction_date.isoformat(), "reliability": 1.0},
            ])
        else:
            evidence_items.append(
                {"source": "bank", "field": "record_presence", "value": "MISSING_IN_BANK", "reliability": 1.0}
            )

        # 3. Reconciliation Match Evidence
        if recon:
            evidence_items.extend([
                {"source": "reconciliation", "field": "match_status", "value": recon.match_status.value, "reliability": 1.0},
                {"source": "reconciliation", "field": "expected_amount", "value": str(recon.expected_amount) if recon.expected_amount is not None else None, "reliability": 1.0},
                {"source": "reconciliation", "field": "actual_amount", "value": str(recon.actual_amount) if recon.actual_amount is not None else None, "reliability": 1.0},
                {"source": "reconciliation", "field": "difference_amount", "value": str(recon.difference_amount) if recon.difference_amount is not None else "0", "reliability": 1.0},
                {"source": "reconciliation", "field": "matching_method", "value": recon.matching_method or "unknown", "reliability": 1.0},
                {"source": "reconciliation", "field": "confidence_score", "value": str(recon.confidence_score) if recon.confidence_score is not None else None, "reliability": 0.95},
            ])

        # 4. Settlement Evidence
        if settlement:
            evidence_items.extend([
                {"source": "settlement", "field": "settlement_reference", "value": settlement.settlement_reference, "reliability": 1.0},
                {"source": "settlement", "field": "gross_amount", "value": str(settlement.gross_amount), "reliability": 1.0},
                {"source": "settlement", "field": "fees", "value": str(settlement.fees), "reliability": 1.0},
                {"source": "settlement", "field": "taxes", "value": str(settlement.taxes), "reliability": 1.0},
                {"source": "settlement", "field": "net_amount", "value": str(settlement.net_amount), "reliability": 1.0},
                {"source": "settlement", "field": "status", "value": settlement.status.value if settlement.status else None, "reliability": 1.0},
            ])
        else:
            evidence_items.append(
                {"source": "settlement", "field": "settlement_batch", "value": "NO_SETTLEMENT_RECORDED", "reliability": 0.8}
            )

        # 5. Exception Evidence
        if exc:
            evidence_items.extend([
                {"source": "exception", "field": "severity", "value": exc.severity.value, "reliability": 1.0},
                {"source": "exception", "field": "category", "value": exc.category, "reliability": 1.0},
                {"source": "exception", "field": "description", "value": exc.description, "reliability": 1.0},
                {"source": "exception", "field": "status", "value": exc.status.value, "reliability": 1.0},
            ])

        # 6. Related History Evidence
        if related_txns:
            evidence_items.append({
                "source": "history",
                "field": "duplicate_candidates_count",
                "value": len(related_txns),
                "reliability": 0.9,
            })
        if related_exceptions:
            evidence_items.append({
                "source": "history",
                "field": "prior_exceptions_count",
                "value": len(related_exceptions),
                "reliability": 0.9,
            })
        if previous_analyses:
            evidence_items.append({
                "source": "history",
                "field": "prior_ai_analyses_count",
                "value": len(previous_analyses),
                "reliability": 0.85,
            })

        return InvestigationContext(
            reconciliation_result=recon,
            transaction=txn,
            bank_transaction=btxn,
            settlement=settlement,
            exception=exc,
            related_transactions=related_txns,
            related_exceptions=related_exceptions,
            previous_ai_analyses=previous_analyses,
            evidence=evidence_items,
        )
