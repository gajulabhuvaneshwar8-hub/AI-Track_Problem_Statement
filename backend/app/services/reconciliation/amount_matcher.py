"""
app/services/reconciliation/amount_matcher.py

Deterministic financial amount matching and discrepancy calculation.
Strictly uses Decimal — never float.
"""

from decimal import Decimal
from typing import Tuple


def compare_amounts(
    expected_amount: Decimal,
    actual_amount: Decimal,
    tolerance: Decimal = Decimal("0.0000"),
) -> Tuple[bool, Decimal]:
    """
    Compare expected and actual amounts with strict Decimal precision.
    Returns: (is_match, difference) where difference = actual - expected.
    """
    exp = Decimal(str(expected_amount))
    act = Decimal(str(actual_amount))
    difference = act - exp
    is_match = abs(difference) <= tolerance
    return is_match, difference


def format_amount_difference(
    expected_amount: Decimal,
    actual_amount: Decimal,
    currency: str = "USD",
) -> str:
    """Format human-readable explanation for an amount mismatch."""
    _, diff = compare_amounts(expected_amount, actual_amount)
    sign = "+" if diff > 0 else ""
    return (
        f"Transaction reference matched, but the bank amount ({actual_amount} {currency}) "
        f"differs from the gateway amount ({expected_amount} {currency}) by {sign}{diff} {currency}."
    )
