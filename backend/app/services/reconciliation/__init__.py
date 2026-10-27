"""
app/services/reconciliation package.

Provides deterministic transaction matching, anomaly detection, confidence scoring,
and reconciliation result orchestration.
"""

from app.services.reconciliation.amount_matcher import compare_amounts, format_amount_difference
from app.services.reconciliation.confidence import calculate_confidence
from app.services.reconciliation.date_matcher import calculate_delay, is_within_date_tolerance
from app.services.reconciliation.duplicate_detector import (
    find_bank_duplicates,
    find_gateway_duplicates,
    normalize_reference,
)
from app.services.reconciliation.matching_engine import MatchCandidate, evaluate_pair
from app.services.reconciliation.reconciliation_engine import ReconciliationEngine
from app.services.reconciliation.reconciliation_service import ReconciliationService
from app.services.reconciliation.result_builder import (
    build_exception_for_candidate,
    build_reconciliation_result,
)

__all__ = [
    "ReconciliationService",
    "ReconciliationEngine",
    "MatchCandidate",
    "evaluate_pair",
    "calculate_confidence",
    "compare_amounts",
    "format_amount_difference",
    "is_within_date_tolerance",
    "calculate_delay",
    "find_gateway_duplicates",
    "find_bank_duplicates",
    "normalize_reference",
    "build_reconciliation_result",
    "build_exception_for_candidate",
]
