"""
app/services/agents/decision_engine.py

Deterministic decision engine for the AI Reconciliation Investigation Agent (Step 7).
Enforces business rules and financial risk policies to categorize investigations into:
  - MONITOR
  - REVIEW
  - ESCALATE

CRITICAL FINANCIAL INTEGRITY CONSTRAINT:
The LLM must NOT override the financial decision rules.
These rules must be deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from app.models.enums import (
    AgentDecision,
    ExceptionSeverity,
    MatchStatus,
    RiskLevel,
    TransactionStatus,
)
from app.services.agents.investigation_context import InvestigationContext

# Threshold constants for financial risk assessment
LARGE_DISCREPANCY_THRESHOLD = Decimal("5000.00")
MODERATE_DISCREPANCY_THRESHOLD = Decimal("500.00")
CRITICAL_AMOUNT_THRESHOLD = Decimal("100000.00")


@dataclass
class DecisionOutcome:
    """Outcome produced by the deterministic decision engine."""

    decision: AgentDecision
    risk_level: RiskLevel
    confidence_score: Decimal
    escalation_required: bool
    rationale: str
    reasons: List[str]


class DecisionEngine:
    """
    Evaluates verified empirical evidence from InvestigationContext and returns
    a deterministic decision (MONITOR, REVIEW, or ESCALATE).
    """

    def evaluate(self, context: InvestigationContext) -> DecisionOutcome:
        reasons: List[str] = []

        recon = context.reconciliation_result
        txn = context.transaction
        btxn = context.bank_transaction
        exc = context.exception

        match_status = recon.match_status if recon else None
        severity = exc.severity if exc else ExceptionSeverity.medium
        diff_amount = Decimal(str(recon.difference_amount)) if (recon and recon.difference_amount is not None) else Decimal("0")
        expected_amt = Decimal(str(recon.expected_amount)) if (recon and recon.expected_amount is not None) else (
            Decimal(str(txn.amount)) if (txn and txn.amount is not None) else Decimal("0")
        )

        txn_status = txn.status if txn else None
        btxn_status = getattr(btxn, "status", None) if btxn else None
        if hasattr(btxn_status, "value"):
            btxn_status = btxn_status.value

        # ------------------------------------------------------------------
        # Rule Set 1: ESCALATE Conditions (Highest Precedence)
        # ------------------------------------------------------------------
        # 1. Critical exception severity
        if severity == ExceptionSeverity.critical:
            reasons.append("Exception has CRITICAL severity flag.")

        # 2. Gateway success + bank failure / reversal
        if txn_status == TransactionStatus.success and btxn_status in ("failed", "reversed"):
            reasons.append("Critical state mismatch: Gateway succeeded but bank transaction failed or reversed.")

        # 3. Large amount discrepancy >= 5,000
        if diff_amount >= LARGE_DISCREPANCY_THRESHOLD:
            reasons.append(f"Large discrepancy of ₹{diff_amount:,.2f} exceeds tolerance limit (₹{LARGE_DISCREPANCY_THRESHOLD}).")

        # 4. High-value transaction (> 100,000) unresolved or missing in bank
        if expected_amt >= CRITICAL_AMOUNT_THRESHOLD and match_status in (
            MatchStatus.missing_in_bank,
            MatchStatus.unresolved,
            MatchStatus.amount_mismatch,
        ):
            reasons.append(f"High-value transaction (₹{expected_amt:,.2f}) has unresolved match status: {match_status.value}.")

        # 5. Suspicious duplicate records found
        if match_status == MatchStatus.duplicate or len(context.related_transactions) > 1:
            reasons.append(f"Suspicious duplicate candidate transactions detected ({len(context.related_transactions)} related).")

        # 6. Repeated failure patterns on same account/order
        if len(context.related_exceptions) >= 2:
            reasons.append(f"Recurring exception pattern: {len(context.related_exceptions)} prior exceptions recorded.")

        if reasons:
            # Deterministic ESCALATE
            risk = RiskLevel.critical if severity == ExceptionSeverity.critical or diff_amount >= LARGE_DISCREPANCY_THRESHOLD else RiskLevel.high
            return DecisionOutcome(
                decision=AgentDecision.escalate,
                risk_level=risk,
                confidence_score=Decimal("0.95"),
                escalation_required=True,
                rationale="; ".join(reasons),
                reasons=reasons,
            )

        # ------------------------------------------------------------------
        # Rule Set 2: REVIEW Conditions (Medium Precedence)
        # ------------------------------------------------------------------
        review_reasons: List[str] = []

        # 1. Medium or High severity exception
        if severity in (ExceptionSeverity.medium, ExceptionSeverity.high):
            review_reasons.append(f"Exception severity is {severity.value.upper()}.")

        # 2. Moderate amount discrepancy between 500 and 5,000
        if MODERATE_DISCREPANCY_THRESHOLD <= diff_amount < LARGE_DISCREPANCY_THRESHOLD:
            review_reasons.append(f"Moderate amount discrepancy of ₹{diff_amount:,.2f} detected.")

        # 3. Incomplete evidence (missing bank transaction or missing gateway transaction)
        if match_status in (MatchStatus.missing_in_bank, MatchStatus.missing_in_gateway):
            review_reasons.append(f"Incomplete ledger pairing: {match_status.value}.")

        # 4. Partial match or unresolved
        if match_status in (MatchStatus.partial_match, MatchStatus.unresolved):
            review_reasons.append(f"Reconciliation result requires manual operator verification ({match_status.value}).")

        # 5. Prior exception on this transaction
        if len(context.related_exceptions) == 1:
            review_reasons.append("One previous exception was noted for this transaction reference.")

        # 6. Missing settlement record
        if not context.settlement and expected_amt > Decimal("1000"):
            review_reasons.append("No corresponding settlement batch discovered for evaluation.")

        if review_reasons:
            risk = RiskLevel.high if severity == ExceptionSeverity.high else RiskLevel.medium
            return DecisionOutcome(
                decision=AgentDecision.review,
                risk_level=risk,
                confidence_score=Decimal("0.85"),
                escalation_required=False,
                rationale="; ".join(review_reasons),
                reasons=review_reasons,
            )

        # ------------------------------------------------------------------
        # Rule Set 3: MONITOR Conditions (Default Low-Risk)
        # ------------------------------------------------------------------
        # Low severity, small or zero discrepancy, high confidence, no suspicious pattern
        return DecisionOutcome(
            decision=AgentDecision.monitor,
            risk_level=RiskLevel.low,
            confidence_score=Decimal("0.92"),
            escalation_required=False,
            rationale="Discrepancy is within acceptable tolerance; standard automated settlement monitoring advised.",
            reasons=["Low discrepancy", "No critical status mismatch", "Single isolated incident"],
        )
