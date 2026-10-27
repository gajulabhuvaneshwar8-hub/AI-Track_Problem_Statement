"""
app/services/ingestion/validators.py

Row-level validators for financial file ingestion.
Returns None if valid, or a RowError object if invalid.
"""

from decimal import Decimal
from typing import Any, Dict, Optional

from app.schemas.ingestion import RowError


def validate_gateway_row(row: Dict[str, Any], row_num: int) -> Optional[RowError]:
    """Validate a single normalized gateway transaction row."""
    ref = row.get("transaction_reference")
    if not ref or not str(ref).strip():
        return RowError(
            row_number=row_num,
            field="transaction_reference",
            error="Missing required transaction_reference.",
            raw_value=ref,
        )

    amount = row.get("amount")
    if amount is None or not isinstance(amount, Decimal):
        return RowError(
            row_number=row_num,
            field="amount",
            error="Invalid or missing amount. Must be a numeric value.",
            raw_value=amount,
        )

    if amount <= Decimal("0"):
        return RowError(
            row_number=row_num,
            field="amount",
            error="Amount must be greater than zero.",
            raw_value=str(amount),
        )

    txn_date = row.get("transaction_date")
    if txn_date is None:
        return RowError(
            row_number=row_num,
            field="transaction_date",
            error="Invalid or missing transaction_date. Could not parse date format.",
            raw_value=row.get("raw_transaction_date"),
        )

    currency = row.get("currency")
    if not currency or len(str(currency).strip()) != 3:
        return RowError(
            row_number=row_num,
            field="currency",
            error="Currency must be a 3-letter ISO code (e.g. USD, EUR).",
            raw_value=currency,
        )

    return None


def validate_bank_row(row: Dict[str, Any], row_num: int) -> Optional[RowError]:
    """Validate a single normalized bank transaction row."""
    ref = row.get("bank_reference")
    if not ref or not str(ref).strip():
        return RowError(
            row_number=row_num,
            field="bank_reference",
            error="Missing required bank_reference.",
            raw_value=ref,
        )

    amount = row.get("amount")
    if amount is None or not isinstance(amount, Decimal):
        return RowError(
            row_number=row_num,
            field="amount",
            error="Invalid or missing amount. Must be a numeric value.",
            raw_value=amount,
        )

    if amount == Decimal("0"):
        return RowError(
            row_number=row_num,
            field="amount",
            error="Bank transaction amount cannot be zero.",
            raw_value=str(amount),
        )

    booking_date = row.get("booking_date")
    if booking_date is None:
        return RowError(
            row_number=row_num,
            field="booking_date",
            error="Invalid or missing booking_date. Could not parse date format.",
            raw_value=row.get("raw_booking_date"),
        )

    currency = row.get("currency")
    if not currency or len(str(currency).strip()) != 3:
        return RowError(
            row_number=row_num,
            field="currency",
            error="Currency must be a 3-letter ISO code (e.g. USD, EUR).",
            raw_value=currency,
        )

    return None


def validate_settlement_row(row: Dict[str, Any], row_num: int) -> Optional[RowError]:
    """Validate a single normalized settlement row."""
    ref = row.get("settlement_reference")
    if not ref or not str(ref).strip():
        return RowError(
            row_number=row_num,
            field="settlement_reference",
            error="Missing required settlement_reference.",
            raw_value=ref,
        )

    gross = row.get("gross_amount")
    if gross is None or not isinstance(gross, Decimal):
        return RowError(
            row_number=row_num,
            field="gross_amount",
            error="Invalid or missing gross_amount.",
            raw_value=gross,
        )

    net = row.get("net_amount")
    if net is None or not isinstance(net, Decimal):
        return RowError(
            row_number=row_num,
            field="net_amount",
            error="Invalid or missing net_amount.",
            raw_value=net,
        )

    settlement_date = row.get("settlement_date")
    if settlement_date is None:
        return RowError(
            row_number=row_num,
            field="settlement_date",
            error="Invalid or missing settlement_date. Could not parse date format.",
            raw_value=row.get("raw_settlement_date"),
        )

    currency = row.get("currency")
    if not currency or len(str(currency).strip()) != 3:
        return RowError(
            row_number=row_num,
            field="currency",
            error="Currency must be a 3-letter ISO code (e.g. USD, EUR).",
            raw_value=currency,
        )

    return None
