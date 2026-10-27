"""
app/services/ingestion/bank_importer.py

Ingests bank statement transaction records from a DataFrame into the bank_transactions table.
"""

import uuid
from typing import List, Optional, Set, Tuple
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.bank_transaction import BankTransaction
from app.schemas.ingestion import RowError
from app.services.ingestion.normalizer import (
    BANK_ALIASES,
    map_columns,
    normalize_bank_status,
    parse_datetime,
    parse_decimal,
)
from app.services.ingestion.validators import validate_bank_row


def import_bank_dataframe(
    df: pd.DataFrame,
    merchant_id: Optional[uuid.UUID],
    db: Session,
) -> Tuple[int, int, int, List[RowError]]:
    """
    Process bank statement DataFrame: map columns, validate, deduplicate, and insert.
    Returns: (imported_count, duplicate_count, invalid_count, errors)
    """
    # Extended aliases for bank statement cross-referencing
    extended_bank_aliases = {
        **BANK_ALIASES,
        "transaction_reference": [
            "transaction_reference", "txn_ref", "gateway_reference",
            "order_reference", "order_id",
        ],
        "bank_name": ["bank_name", "bank", "institution", "source_bank"],
    }

    col_map = map_columns(df, extended_bank_aliases)

    ref_col = col_map.get("bank_reference")
    amt_col = col_map.get("amount")
    date_col = col_map.get("booking_date")

    errors: List[RowError] = []

    if not ref_col:
        errors.append(
            RowError(
                row_number=1,
                field="bank_reference",
                error="Required column 'bank_reference' (or alias) not found in file.",
                raw_value=list(df.columns),
            )
        )
        return 0, 0, len(df), errors

    # Check existing bank references in DB
    raw_refs = [
        str(val).strip()
        for val in df[ref_col].dropna()
        if str(val).strip()
    ]

    existing_refs: Set[str] = set()
    if raw_refs:
        stmt = select(BankTransaction.bank_reference).where(
            BankTransaction.bank_reference.in_(raw_refs)
        )
        existing_refs = set(db.execute(stmt).scalars().all())

    seen_in_file: Set[str] = set()
    to_insert: List[BankTransaction] = []
    duplicate_count = 0
    invalid_count = 0

    desc_col = col_map.get("description")
    curr_col = col_map.get("currency")
    status_col = col_map.get("status")
    bank_name_col = col_map.get("bank_name")
    txn_ref_col = col_map.get("transaction_reference")

    for idx, (_, row) in enumerate(df.iterrows(), start=2):
        raw_ref = str(row[ref_col]).strip() if ref_col and pd.notna(row.get(ref_col)) else None
        raw_amt = row.get(amt_col) if amt_col else None
        raw_date = row.get(date_col) if date_col else None

        normalized_row = {
            "bank_reference": raw_ref,
            "transaction_reference": str(row[txn_ref_col]).strip() if txn_ref_col and pd.notna(row.get(txn_ref_col)) else None,
            "amount": parse_decimal(raw_amt),
            "currency": str(row.get(curr_col)).strip().upper() if curr_col and pd.notna(row.get(curr_col)) else "USD",
            "booking_date": parse_datetime(raw_date),
            "description": str(row[desc_col]).strip() if desc_col and pd.notna(row.get(desc_col)) else None,
            "bank_name": str(row[bank_name_col]).strip() if bank_name_col and pd.notna(row.get(bank_name_col)) else "Bank",
            "status": str(normalize_bank_status(row.get(status_col) if status_col else None).value),
            "raw_booking_date": raw_date,
        }

        # 1. Validation
        val_err = validate_bank_row(normalized_row, idx)
        if val_err:
            invalid_count += 1
            errors.append(val_err)
            continue

        # 2. Deduplication
        ref = normalized_row["bank_reference"]
        if ref in seen_in_file:
            duplicate_count += 1
            errors.append(
                RowError(
                    row_number=idx,
                    field="bank_reference",
                    error=f"Duplicate bank reference '{ref}' found within the uploaded file.",
                    raw_value=ref,
                )
            )
            continue

        if ref in existing_refs:
            duplicate_count += 1
            errors.append(
                RowError(
                    row_number=idx,
                    field="bank_reference",
                    error=f"Bank reference '{ref}' already exists in database.",
                    raw_value=ref,
                )
            )
            continue

        seen_in_file.add(ref)

        bank_txn = BankTransaction(
            bank_reference=ref,
            transaction_reference=normalized_row["transaction_reference"],
            amount=normalized_row["amount"],
            transaction_date=normalized_row["booking_date"],
            description=normalized_row["description"],
            bank_name=normalized_row["bank_name"],
            status=normalized_row["status"],
        )
        to_insert.append(bank_txn)

    if to_insert:
        db.add_all(to_insert)

    return len(to_insert), duplicate_count, invalid_count, errors
