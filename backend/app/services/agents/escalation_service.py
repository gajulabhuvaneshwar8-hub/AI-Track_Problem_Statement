"""
app/services/agents/escalation_service.py

EscalationService for the AI Reconciliation Investigation Agent (Step 7).
Generates escalation recommendations and routes investigations to the appropriate operational team:
  - Finance Operations
  - Payment Operations
  - Risk Team
  - Engineering
  - Merchant Support

NOTE:
Does NOT actually dispatch external emails or Slack messages yet.
Only creates escalation records and recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.models.enums import EscalationTeam, ExceptionSeverity, MatchStatus, TransactionStatus
from app.schemas.agent import EscalationResponse
from app.services.agents.investigation_context import InvestigationContext


@dataclass
class EscalationRecommendation:
    """Structured escalation suggestion generated for an investigation."""

    action: str
    priority: str
    reason: str
    recommended_team: str


class EscalationService:
    """
    Evaluates an InvestigationContext to determine team ownership, urgency, and routing reasons.
    """

    def generate_recommendation(
        self,
        context: InvestigationContext,
        decision_rationale: Optional[str] = None,
    ) -> EscalationRecommendation:
        exc = context.exception
        recon = context.reconciliation_result
        txn = context.transaction
        btxn = context.bank_transaction

        severity = exc.severity if exc else ExceptionSeverity.medium
        match_status = recon.match_status if recon else None
        txn_status = txn.status if txn else None
        btxn_status = getattr(btxn, "status", None) if btxn else None
        if hasattr(btxn_status, "value"):
            btxn_status = btxn_status.value

        diff_amount = Decimal(str(recon.difference_amount)) if (recon and recon.difference_amount is not None) else Decimal("0")

        # Priority calculation
        if severity == ExceptionSeverity.critical or (txn_status == TransactionStatus.success and btxn_status in ("failed", "reversed")):
            priority = "CRITICAL"
        elif severity == ExceptionSeverity.high or diff_amount >= Decimal("5000.00"):
            priority = "HIGH"
        elif severity == ExceptionSeverity.medium:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # Team routing logic
        if match_status == MatchStatus.duplicate or len(context.related_transactions) > 1:
            team = EscalationTeam.risk_team.value
            reason = "Suspicious duplicate transaction detected requiring fraud & risk assessment."
        elif txn_status == TransactionStatus.success and btxn_status in ("failed", "reversed"):
            team = EscalationTeam.finance_operations.value
            reason = "Gateway transaction succeeded but bank transaction failed or reversed; customer funds unaccounted."
        elif match_status == MatchStatus.amount_mismatch:
            team = EscalationTeam.finance_operations.value
            reason = f"Amount mismatch of ₹{diff_amount:,.2f} between gateway and bank statement requires manual reconciliation ledger adjustment."
        elif match_status == MatchStatus.missing_in_bank:
            team = EscalationTeam.payment_operations.value
            reason = "Transaction authorized by gateway but unacknowledged on bank statement after clearing window."
        elif match_status == MatchStatus.missing_in_gateway:
            team = EscalationTeam.engineering.value
            reason = "Orphan bank credit record with no matching gateway transaction; likely webhook/API ingestion failure."
        elif severity == ExceptionSeverity.critical:
            team = EscalationTeam.finance_operations.value
            reason = "Critical severity exception requiring immediate controller review."
        else:
            team = EscalationTeam.merchant_support.value
            reason = decision_rationale or "Reconciliation variance detected; merchant statement confirmation advised."

        if decision_rationale and reason not in decision_rationale:
            reason = f"{reason} ({decision_rationale})"

        return EscalationRecommendation(
            action="ESCALATE",
            priority=priority,
            reason=reason,
            recommended_team=team,
        )

    def to_schema(self, recommendation: EscalationRecommendation) -> EscalationResponse:
        """Converts internal recommendation to public schema."""
        return EscalationResponse(
            action=recommendation.action,
            priority=recommendation.priority,
            reason=recommendation.reason,
            recommended_team=recommendation.recommended_team,
        )
