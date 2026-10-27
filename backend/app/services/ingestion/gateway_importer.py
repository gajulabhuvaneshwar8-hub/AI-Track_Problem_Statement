"""
app/services/ingestion/gateway_importer.py

Ingests payment gateway transaction records from a DataFrame into the transactions table.
"""

import uuid
from typing import List, Optional, Set, Tuple
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import TransactionSource
from app.models.transaction import Transaction
from app.schemas.ingestion import RowError
from app.services.ingestion.normalizer import (
    GATEWAY_ALIASES,
    map_columns,
    normalize_currency,
    normalize_gateway_status,
    parse_datetime,
    parse_decimal,
)
from app.services.ingestion.validators import validate_gateway_row


def import_gateway_dataframe(
    df: pd.DataFrame,
    merchant_id: Optional[uuid.UUID],
    db: Session,
) -> Tuple[int, int, int, List[RowError]]:
    """
    Process gateway DataFrame: map columns, validate, deduplicate, and insert.
    Returns: (imported_count, duplicate_count, invalid_count, errors)
    """
    col_map = map_columns(df, GATEWAY_ALIASES)

    ref_col = col_map.get("transaction_reference")
    amt_col = col_map.get("amount")
    date_col = col_map.get("transaction_date")

    errors: List[RowError] = []

    if not ref_col:
        errors.append(
            RowError(
                row_number=1,
                field="transaction_reference",
                error="Required column 'transaction_reference' (or alias) not found in file.",
                raw_value=list(df.columns),
            )
        )
        return 0, 0, len(df), errors

    # Extract all candidate references from file to check duplicates in DB
    raw_refs = [
        str(val).strip()
        for val in df[ref_col].dropna()
        if str(val).strip()
    ]

    existing_refs: Set[str] = set()
    if raw_refs:
        stmt = select(Transaction.transaction_reference).where(
            Transaction.transaction_reference.in_(raw_refs)
        )
        existing_refs = set(db.execute(stmt).scalars().all())

    seen_in_file: Set[str] = set()
    to_insert: List[Transaction] = []
    duplicate_count = 0
    invalid_count = 0

    order_col = col_map.get("order_reference")
    cust_col = col_map.get("customer_reference")
    curr_col = col_map.get("currency")
    method_col = col_map.get("payment_method")
    gateway_col = col_map.get("gateway")
    status_col = col_map.get("status")

    for idx, (_, row) in enumerate(df.iterrows(), start=2):  # row 1 is header
        raw_ref = str(row[ref_col]).strip() if ref_col and pd.notna(row.get(ref_col)) else None
        raw_amt = row.get(amt_col) if amt_col else None
        raw_date = row.get(date_col) if date_col else None

        normalized_row = {
            "transaction_reference": raw_ref,
            "order_reference": str(row[order_col]).strip() if order_col and pd.notna(row.get(order_col)) else None,
            "customer_reference": str(row[cust_col]).strip() if cust_col and pd.notna(row.get(cust_col)) else None,
            "amount": parse_decimal(raw_amt),
            "currency": normalize_currency(row.get(curr_col) if curr_col else None),
            "transaction_date": parse_datetime(raw_date),
            "payment_method": str(row[method_col]).strip() if method_col and pd.notna(row.get(method_col)) else None,
            "gateway": str(row[gateway_col]).strip() if gateway_col and pd.notna(row.get(gateway_col)) else "gateway",
            "status": normalize_gateway_status(row.get(status_col) if status_col else None),
            "raw_transaction_date": raw_date,
        }

        # 1. Validation
        val_err = validate_gateway_row(normalized_row, idx)
        if val_err:
            invalid_count += 1
            errors.append(val_err)
            continue

        # 2. Deduplication check
        ref = normalized_row["transaction_reference"]
        if ref in seen_in_file:
            duplicate_count += 1
            errors.append(
                RowError(
                    row_number=idx,
                    field="transaction_reference",
                    error=f"Duplicate transaction reference '{ref}' found within the uploaded file.",
                    raw_value=ref,
                )
            )
            continue

        if ref in existing_refs:
            duplicate_count += 1
            errors.append(
                RowError(
                    row_number=idx,
                    field="transaction_reference",
                    error=f"Transaction reference '{ref}' already exists in database.",
                    raw_value=ref,
                )
            )
            continue

        seen_in_file.add(ref)

        txn = Transaction(
            transaction_reference=ref,
            order_reference=normalized_row["order_reference"],
            customer_reference=normalized_row["customer_reference"],
            merchant_id=merchant_id,
            amount=normalized_row["amount"],
            currency=normalized_row["currency"],
            transaction_date=normalized_row["transaction_date"],
            payment_method=normalized_row["payment_method"],
            gateway=normalized_row["gateway"],
            status=normalized_row["status"],
            source=TransactionSource.gateway,
        )
        to_insert.append(txn)

    if to_insert:
        db.add_all(to_insert)

    return len(to_insert), duplicate_count, invalid_count, errors
