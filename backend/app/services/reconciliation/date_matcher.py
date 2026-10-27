"""
app/services/reconciliation/date_matcher.py

Date comparison, tolerance checking, and settlement delay detection.
"""

from datetime import datetime
from typing import Tuple

DEFAULT_DATE_TOLERANCE_DAYS = 1
DEFAULT_DELAY_THRESHOLD_DAYS = 1
DEFAULT_SEVERE_DELAY_THRESHOLD_DAYS = 3


def is_within_date_tolerance(
    date1: datetime,
    date2: datetime,
    tolerance_days: int = DEFAULT_DATE_TOLERANCE_DAYS,
) -> bool:
    """Check whether two timestamps are within a configured tolerance window."""
    diff_seconds = abs((date1 - date2).total_seconds())
    return diff_seconds <= (tolerance_days * 86400)


def calculate_delay(
    gateway_date: datetime,
    bank_date: datetime,
    delay_threshold_days: int = DEFAULT_DELAY_THRESHOLD_DAYS,
    severe_threshold_days: int = DEFAULT_SEVERE_DELAY_THRESHOLD_DAYS,
) -> Tuple[bool, bool, float]:
    """
    Calculate the settlement delay from gateway date to bank posting date.
    Returns: (is_delayed, is_severely_delayed, delay_days)
    """
    delta_seconds = (bank_date - gateway_date).total_seconds()
    delay_days = delta_seconds / 86400.0

    is_del = delay_days > delay_threshold_days
    is_sev = delay_days > severe_threshold_days

    return is_del, is_sev, delay_days
