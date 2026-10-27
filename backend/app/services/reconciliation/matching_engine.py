"""
app/services/reconciliation/matching_engine.py

Core deterministic matching hierarchy for comparing Gateway transactions with Bank transactions:
Level 1: Exact reference
Level 2: Normalized reference
Level 3: Amount + Date fallback match (single unique candidate or unresolved)
Also detects amount mismatches, settlement delays, and status contradictions.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from app.models.bank_transaction import BankTransaction
from app.models.enums import MatchStatus, TransactionStatus
from app.models.transaction import Transaction
from app.services.reconciliation.amount_matcher import compare_amounts, format_amount_difference
from app.services.reconciliation.confidence import calculate_confidence
from app.services.reconciliation.date_matcher import calculate_delay, is_within_date_tolerance
from app.services.reconciliation.duplicate_detector import normalize_reference


class MatchCandidate:
    """Represents a potential or confirmed match between a gateway and bank transaction."""

    def __init__(
        self,
        transaction: Optional[Transaction],
        bank_transaction: Optional[BankTransaction],
        match_status: MatchStatus,
        confidence_score: Decimal,
        matching_method: str,
        expected_amount: Optional[Decimal],
        actual_amount: Optional[Decimal],
        difference_amount: Optional[Decimal],
        explanation: str,
        is_delayed: bool = False,
        is_severely_delayed: bool = False,
        delay_days: float = 0.0,
        has_status_mismatch: bool = False,
        has_multiple_candidates: bool = False,
    ):
        self.transaction = transaction
        self.bank_transaction = bank_transaction
        self.match_status = match_status
        self.confidence_score = confidence_score
        self.matching_method = matching_method
        self.expected_amount = expected_amount
        self.actual_amount = actual_amount
        self.difference_amount = difference_amount
        self.explanation = explanation
        self.is_delayed = is_delayed
        self.is_severely_delayed = is_severely_delayed
        self.delay_days = delay_days
        self.has_status_mismatch = has_status_mismatch
        self.has_multiple_candidates = has_multiple_candidates


def _is_bank_failure(bank_txn: BankTransaction) -> bool:
    """Check if bank statement status indicates failure or reversal."""
    if not bank_txn.status:
        return False
    status_lower = bank_txn.status.lower()
    return any(term in status_lower for term in ("fail", "revers", "declined", "void"))


def evaluate_pair(
    gtxn: Transaction,
    btxn: BankTransaction,
    method_prefix: str,
) -> MatchCandidate:
    """
    Evaluate a candidate pair whose references matched (exact or normalized).
    Checks status mismatch, amount difference, and settlement delays.
    """
    # 1. Status conflict: Gateway success vs Bank failure
    if gtxn.status == TransactionStatus.success and _is_bank_failure(btxn):
        return MatchCandidate(
            transaction=gtxn,
            bank_transaction=btxn,
            match_status=MatchStatus.unresolved,
            confidence_score=Decimal("0.3000"),
            matching_method=method_prefix,
            expected_amount=gtxn.amount,
            actual_amount=btxn.amount,
            difference_amount=btxn.amount - gtxn.amount,
            explanation=(
                "Gateway indicates a successful transaction while the corresponding "
                "bank record indicates failure."
            ),
            has_status_mismatch=True,
        )

    # 2. Amount comparison
    is_amt_match, diff = compare_amounts(gtxn.amount, btxn.amount)

    # 3. Date delay comparison
    is_del, is_sev_del, delay_days = calculate_delay(
        gtxn.transaction_date, btxn.transaction_date
    )

    curr = gtxn.currency or "USD"

    if not is_amt_match:
        # Amount mismatch
        confidence = calculate_confidence(method_prefix, amount_matches=False)
        return MatchCandidate(
            transaction=gtxn,
            bank_transaction=btxn,
            match_status=MatchStatus.amount_mismatch,
            confidence_score=confidence,
            matching_method=method_prefix,
            expected_amount=gtxn.amount,
            actual_amount=btxn.amount,
            difference_amount=diff,
            explanation=format_amount_difference(gtxn.amount, btxn.amount, curr),
            is_delayed=is_del,
            is_severely_delayed=is_sev_del,
            delay_days=delay_days,
        )

    # Both reference and amount match
    if is_del:
        confidence = calculate_confidence(method_prefix, amount_matches=True, is_delayed=True)
        method = f"{method_prefix}_delayed"
        explanation = (
            f"Transaction reference and amount ({gtxn.amount} {curr}) matched with a "
            f"settlement delay of {delay_days:.1f} days."
        )
    else:
        confidence = calculate_confidence(method_prefix, amount_matches=True, is_delayed=False)
        method = method_prefix
        explanation = (
            f"Transaction matched successfully with exact amount ({gtxn.amount} {curr}) "
            f"via {method_prefix.replace('_', ' ')}."
        )

    return MatchCandidate(
        transaction=gtxn,
        bank_transaction=btxn,
        match_status=MatchStatus.matched,
        confidence_score=confidence,
        matching_method=method,
        expected_amount=gtxn.amount,
        actual_amount=btxn.amount,
        difference_amount=diff,
        explanation=explanation,
        is_delayed=is_del,
        is_severely_delayed=is_sev_del,
        delay_days=delay_days,
    )
