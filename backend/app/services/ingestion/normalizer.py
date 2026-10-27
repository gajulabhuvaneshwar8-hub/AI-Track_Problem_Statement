"""
app/services/ingestion/normalizer.py

Normalizes raw data from CSV/Excel dataframes into standardized dictionaries
ready for validation and database insertion.
"""

import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
import pandas as pd
from dateutil import parser as date_parser

from app.models.enums import (
    BankTransactionStatus,
    SettlementStatus,
    TransactionSource,
    TransactionStatus,
)

# ---------------------------------------------------------------------------
# Header / Field alias mappings
# ---------------------------------------------------------------------------

GATEWAY_ALIASES = {
    "transaction_reference": [
        "transaction_reference", "transaction_ref", "txn_ref", "reference",
        "tx_id", "transaction_id", "id", "payment_reference",
    ],
    "order_reference": [
        "order_reference", "order_ref", "order_id", "merchant_order_id",
    ],
    "customer_reference": [
        "customer_reference", "customer_ref", "cust_ref", "customer_id",
        "customer_email", "email",
    ],
    "amount": [
        "amount", "amt", "total_amount", "value", "payment_amount",
    ],
    "currency": [
        "currency", "curr", "ccy",
    ],
    "transaction_date": [
        "transaction_date", "date", "created_at", "timestamp", "txn_date", "datetime",
    ],
    "payment_method": [
        "payment_method", "method", "pay_method", "type", "payment_type",
    ],
    "gateway": [
        "gateway", "provider", "gateway_name", "processor",
    ],
    "status": [
        "status", "state", "txn_status", "payment_status",
    ],
}

BANK_ALIASES = {
    "bank_reference": [
        "bank_reference", "bank_ref", "reference", "trans_id", "txn_ref",
        "txn_id", "utr", "transaction_reference", "ref_no", "id",
    ],
    "amount": [
        "amount", "amt", "credit", "debit", "value", "transaction_amount",
    ],
    "booking_date": [
        "booking_date", "date", "post_date", "transaction_date", "value_date", "txn_date",
    ],
    "value_date": [
        "value_date", "val_date",
    ],
    "description": [
        "description", "narration", "memo", "details", "particulars", "remarks",
    ],
    "currency": [
        "currency", "curr", "ccy",
    ],
    "status": [
        "status", "state", "bank_status",
    ],
}

SETTLEMENT_ALIASES = {
    "settlement_reference": [
        "settlement_reference", "settlement_ref", "batch_ref", "payout_id",
        "reference", "id", "settlement_id",
    ],
    "gross_amount": [
        "gross_amount", "gross_amt", "amount", "total_amount",
    ],
    "net_amount": [
        "net_amount", "net_amt", "payout_amount", "net_payout",
    ],
    "fee_amount": [
        "fee_amount", "fee_amt", "fees", "fee",
    ],
    "currency": [
        "currency", "curr", "ccy",
    ],
    "settlement_date": [
        "settlement_date", "date", "payout_date", "created_at",
    ],
    "period_start": [
        "period_start", "start_date",
    ],
    "period_end": [
        "period_end", "end_date",
    ],
    "status": [
        "status", "state",
    ],
}


def map_columns(df: pd.DataFrame, alias_map: Dict[str, List[str]]) -> Dict[str, str]:
    """
    Find which DataFrame column matches which canonical field name.
    Returns dict {canonical_field: actual_col_name}.
    """
    col_mapping: Dict[str, str] = {}
    normalized_cols = {
        re.sub(r"[^a-zA-Z0-9]", "", str(c).lower()): c for c in df.columns
    }

    for canonical, aliases in alias_map.items():
        for alias in aliases:
            norm_alias = re.sub(r"[^a-zA-Z0-9]", "", alias.lower())
            if norm_alias in normalized_cols:
                col_mapping[canonical] = normalized_cols[norm_alias]
                break

    return col_mapping


def parse_decimal(val: Any) -> Optional[Decimal]:
    """Parse raw value to Decimal, stripping currency symbols and commas."""
    if val is None or pd.isna(val):
        return None
    val_str = str(val).strip()
    if not val_str:
        return None
    # Remove currency symbols, commas, spaces
    val_clean = re.sub(r"[^\d.-]", "", val_str)
    if not val_clean:
        return None
    try:
        return Decimal(val_clean)
    except InvalidOperation:
        return None


def parse_datetime(val: Any) -> Optional[datetime]:
    """Parse raw value to UTC timezone-aware datetime."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)

    val_str = str(val).strip()
    if not val_str:
        return None

    try:
        dt = date_parser.parse(val_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None


def normalize_currency(val: Any, default: str = "USD") -> str:
    """Normalize currency string to 3-letter uppercase code."""
    if val is None or pd.isna(val):
        return default
    curr_str = str(val).strip().upper()
    if len(curr_str) == 3:
        return curr_str
    return default


def normalize_gateway_status(val: Any) -> TransactionStatus:
    """Normalize status string to TransactionStatus enum."""
    if val is None or pd.isna(val):
        return TransactionStatus.success
    s = str(val).strip().lower()
    if "fail" in s or "declin" in s or "reject" in s:
        return TransactionStatus.failed
    if "pend" in s or "process" in s:
        return TransactionStatus.pending
    if "refund" in s:
        return TransactionStatus.refunded
    if "disput" in s or "chargeback" in s:
        return TransactionStatus.disputed
    return TransactionStatus.success


def normalize_bank_status(val: Any) -> BankTransactionStatus:
    """Normalize status string to BankTransactionStatus enum."""
    if val is None or pd.isna(val):
        return BankTransactionStatus.posted
    s = str(val).strip().lower()
    if "pend" in s:
        return BankTransactionStatus.pending
    if "revers" in s or "void" in s:
        return BankTransactionStatus.reversed
    return BankTransactionStatus.posted


def normalize_settlement_status(val: Any) -> SettlementStatus:
    """Normalize status string to SettlementStatus enum."""
    if val is None or pd.isna(val):
        return SettlementStatus.settled
    s = str(val).strip().lower()
    if "pend" in s:
        return SettlementStatus.pending
    if "fail" in s:
        return SettlementStatus.failed
    return SettlementStatus.settled
