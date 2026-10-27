"""
app/services/reconciliation/result_builder.py

Builds ReconciliationResult and PaymentException ORM records from MatchCandidates.
Ensures idempotency by checking for existing records.
"""

from decimal import Decimal
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import ExceptionSeverity, ExceptionStatus, MatchStatus
from app.models.exception import PaymentException
from app.models.reconciliation_result import ReconciliationResult
from app.services.reconciliation.matching_engine import MatchCandidate


def build_reconciliation_result(
    candidate: MatchCandidate,
    existing_result: Optional[ReconciliationResult] = None,
) -> ReconciliationResult:
    """Create or update a ReconciliationResult instance from a MatchCandidate."""
    result = existing_result or ReconciliationResult()

    result.transaction_id = candidate.transaction.id if candidate.transaction else None
    result.bank_transaction_id = (
        candidate.bank_transaction.id if candidate.bank_transaction else None
    )
    result.match_status = candidate.match_status
    result.confidence_score = candidate.confidence_score
    result.expected_amount = candidate.expected_amount
    result.actual_amount = candidate.actual_amount
    result.difference_amount = candidate.difference_amount
    result.matching_method = candidate.matching_method
    result.explanation = candidate.explanation

    return result


def build_exception_for_candidate(
    candidate: MatchCandidate,
    reconciliation_id: Optional[ReconciliationResult] = None,
) -> Optional[PaymentException]:
    """
    Determine if a PaymentException should be created for this match outcome.
    Returns a new PaymentException instance or None if no exception is needed.
    """
    status = candidate.match_status
    ref = (
        candidate.transaction.transaction_reference
        if candidate.transaction
        else (
            candidate.bank_transaction.bank_reference
            if candidate.bank_transaction
            else "N/A"
        )
    )
    curr = (
        candidate.transaction.currency
        if candidate.transaction
        else "USD"
    )

    # 1. Status Mismatch: Critical
    if candidate.has_status_mismatch:
        return PaymentException(
            reconciliation_id=reconciliation_id,
            severity=ExceptionSeverity.critical,
            category="status_mismatch",
            title=f"Gateway success vs Bank failure for {ref}",
            description=(
                "Gateway indicates a successful transaction while the corresponding "
                "bank record indicates failure."
            ),
            recommended_action="Immediately verify the payment state and settlement status.",
            status=ExceptionStatus.open,
        )

    # 2. Missing in Bank: High
    if status == MatchStatus.missing_in_bank:
        return PaymentException(
            reconciliation_id=reconciliation_id,
            severity=ExceptionSeverity.high,
            category="missing_transaction",
            title=f"Gateway transaction {ref} missing in bank statement",
            description=(
                f"Gateway recorded payment of {candidate.expected_amount} {curr}, "
                f"but no bank statement credit was found."
            ),
            recommended_action=(
                "Verify whether the payment was successfully processed by the bank "
                "and check settlement records."
            ),
            status=ExceptionStatus.open,
        )

    # 3. Missing in Gateway: High
    if status == MatchStatus.missing_in_gateway:
        return PaymentException(
            reconciliation_id=reconciliation_id,
            severity=ExceptionSeverity.high,
            category="missing_transaction",
            title=f"Bank transaction {ref} missing in gateway records",
            description=(
                f"Bank statement records transaction of {candidate.actual_amount} {curr}, "
                f"but no corresponding gateway transaction exists."
            ),
            recommended_action=(
                "Verify whether this bank transaction belongs to the merchant and "
                "identify the corresponding order/payment record."
            ),
            status=ExceptionStatus.open,
        )

    # 4. Amount Mismatch: High
    if status == MatchStatus.amount_mismatch:
        return PaymentException(
            reconciliation_id=reconciliation_id,
            severity=ExceptionSeverity.high,
            category="amount_mismatch",
            title=f"Amount mismatch for {ref}",
            description=candidate.explanation,
            recommended_action=(
                "Investigate fee deductions, gateway processing charges, or FX differences."
            ),
            status=ExceptionStatus.open,
        )

    # 5. Duplicate: High
    if status == MatchStatus.duplicate:
        return PaymentException(
            reconciliation_id=reconciliation_id,
            severity=ExceptionSeverity.high,
            category="duplicate_transaction",
            title=f"Duplicate transaction detected: {ref}",
            description=candidate.explanation,
            recommended_action=(
                "Review duplicate payment records and verify whether both transactions are legitimate."
            ),
            status=ExceptionStatus.open,
        )

    # 6. Unresolved (e.g. multiple candidates fallback): Medium
    if status == MatchStatus.unresolved:
        return PaymentException(
            reconciliation_id=reconciliation_id,
            severity=ExceptionSeverity.medium,
            category="unresolved_match",
            title=f"Ambiguous candidates for {ref}",
            description=candidate.explanation,
            recommended_action=(
                "Manually inspect bank statement lines to identify the matching deposit."
            ),
            status=ExceptionStatus.open,
        )

    # 7. Severe settlement delay (> 3 days): Medium
    if candidate.is_severely_delayed:
        return PaymentException(
            reconciliation_id=reconciliation_id,
            severity=ExceptionSeverity.medium,
            category="settlement_delay",
            title=f"Settlement delay for {ref}",
            description=(
                f"Settlement delay of {candidate.delay_days:.1f} days exceeded the 3-day threshold."
            ),
            recommended_action="Review the payment processing and settlement timeline.",
            status=ExceptionStatus.open,
        )

    return None
