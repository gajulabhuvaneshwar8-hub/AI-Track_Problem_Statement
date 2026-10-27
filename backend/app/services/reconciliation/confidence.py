"""
app/services/reconciliation/confidence.py

Deterministic confidence scoring for payment reconciliation results.
Confidence scores are strictly bounded in [0.0000, 1.0000].
"""

from decimal import Decimal

# Base deterministic scoring constants
SCORE_EXACT_REFERENCE = Decimal("1.0000")
SCORE_NORMALIZED_REFERENCE = Decimal("0.9500")
SCORE_REFERENCE_AMOUNT_MISMATCH = Decimal("0.9000")
SCORE_DELAYED_REFERENCE_MATCH = Decimal("0.8500")
SCORE_AMOUNT_DATE_FALLBACK = Decimal("0.8000")
SCORE_UNRESOLVED_CANDIDATES = Decimal("0.3000")
SCORE_ZERO = Decimal("0.0000")


def calculate_confidence(
    matching_method: str,
    amount_matches: bool,
    is_delayed: bool = False,
    is_unresolved: bool = False,
) -> Decimal:
    """
    Determine the confidence score based on the matching method and match attributes.
    Returns a Decimal rounded to 4 decimal places, clamped between 0.0000 and 1.0000.
    """
    if is_unresolved:
        return SCORE_UNRESOLVED_CANDIDATES

    if matching_method in ("no_bank_match", "no_gateway_match", "duplicate"):
        return SCORE_ZERO

    if matching_method == "exact_reference":
        if not amount_matches:
            score = SCORE_REFERENCE_AMOUNT_MISMATCH
        elif is_delayed:
            score = SCORE_DELAYED_REFERENCE_MATCH
        else:
            score = SCORE_EXACT_REFERENCE
    elif matching_method == "normalized_reference":
        if not amount_matches:
            score = Decimal("0.8800")
        elif is_delayed:
            score = Decimal("0.8200")
        else:
            score = SCORE_NORMALIZED_REFERENCE
    elif matching_method in ("exact_reference_delayed", "normalized_reference_delayed"):
        score = SCORE_DELAYED_REFERENCE_MATCH
    elif matching_method == "amount_date_fallback":
        score = SCORE_AMOUNT_DATE_FALLBACK
    else:
        score = SCORE_ZERO

    # Clamp to [0.0000, 1.0000]
    return max(Decimal("0.0000"), min(Decimal("1.0000"), score))
