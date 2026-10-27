"""
app/services/ingestion/settlement_importer.py

Ingests settlement batch records from a DataFrame into the settlements table.
"""

from decimal import Decimal
import uuid
from typing import List, Optional, Set, Tuple
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.settlement import Settlement
from app.schemas.ingestion import RowError
from app.services.ingestion.normalizer import (
    SETTLEMENT_ALIASES,
    map_columns,
    normalize_settlement_status,
    parse_datetime,
    parse_decimal,
)
from app.services.ingestion.validators import validate_settlement_row


def import_settlement_dataframe(
    df: pd.DataFrame,
    merchant_id: Optional[uuid.UUID],
    db: Session,
) -> Tuple[int, int, int, List[RowError]]:
    """
    Process settlement DataFrame: map columns, validate, deduplicate, and insert.
    Returns: (imported_count, duplicate_count, invalid_count, errors)
    """
    # Extended aliases for settlements
    extended_aliases = {
        **SETTLEMENT_ALIASES,
        "taxes": ["taxes", "tax", "vat"],
        "refunds": ["refunds", "refund_amount"],
        "chargebacks": ["chargebacks", "chargeback_amount", "disputes"],
    }

    col_map = map_columns(df, extended_aliases)

    ref_col = col_map.get("settlement_reference")
    gross_col = col_map.get("gross_amount")
    net_col = col_map.get("net_amount")
    date_col = col_map.get("settlement_date")

    errors: List[RowError] = []

    if not ref_col:
        errors.append(
            RowError(
                row_number=1,
                field="settlement_reference",
                error="Required column 'settlement_reference' (or alias) not found in file.",
                raw_value=list(df.columns),
            )
        )
        return 0, 0, len(df), errors

    # Check existing references in DB
    raw_refs = [
        str(val).strip()
        for val in df[ref_col].dropna()
        if str(val).strip()
    ]

    existing_refs: Set[str] = set()
    if raw_refs:
        stmt = select(Settlement.settlement_reference).where(
            Settlement.settlement_reference.in_(raw_refs)
        )
        existing_refs = set(db.execute(stmt).scalars().all())

    seen_in_file: Set[str] = set()
    to_insert: List[Settlement] = []
    duplicate_count = 0
    invalid_count = 0

    fee_col = col_map.get("fee_amount")
    taxes_col = col_map.get("taxes")
    refunds_col = col_map.get("refunds")
    chargebacks_col = col_map.get("chargebacks")
    status_col = col_map.get("status")
    curr_col = col_map.get("currency")

    for idx, (_, row) in enumerate(df.iterrows(), start=2):
        raw_ref = str(row[ref_col]).strip() if ref_col and pd.notna(row.get(ref_col)) else None
        raw_gross = row.get(gross_col) if gross_col else None
        raw_net = row.get(net_col) if net_col else None
        raw_date = row.get(date_col) if date_col else None

        gross = parse_decimal(raw_gross)
        net = parse_decimal(raw_net)
        fee = parse_decimal(row.get(fee_col)) if fee_col else Decimal("0")
        if fee is None:
            fee = Decimal("0")

        taxes = parse_decimal(row.get(taxes_col)) if taxes_col else Decimal("0")
        if taxes is None:
            taxes = Decimal("0")

        refunds = parse_decimal(row.get(refunds_col)) if refunds_col else Decimal("0")
        if refunds is None:
            refunds = Decimal("0")

        chargebacks = parse_decimal(row.get(chargebacks_col)) if chargebacks_col else Decimal("0")
        if chargebacks is None:
            chargebacks = Decimal("0")

        # If net_amount wasn't provided or empty, but gross and fees are present:
        if net is None and gross is not None:
            net = gross - fee - taxes - refunds - chargebacks

        normalized_row = {
            "settlement_reference": raw_ref,
            "gross_amount": gross,
            "net_amount": net,
            "fee_amount": fee,
            "taxes": taxes,
            "refunds": refunds,
            "chargebacks": chargebacks,
            "settlement_date": parse_datetime(raw_date),
            "currency": str(row.get(curr_col)).strip().upper() if curr_col and pd.notna(row.get(curr_col)) else "USD",
            "status": normalize_settlement_status(row.get(status_col) if status_col else None),
            "raw_settlement_date": raw_date,
        }

        # 1. Validation
        val_err = validate_settlement_row(normalized_row, idx)
        if val_err:
            invalid_count += 1
            errors.append(val_err)
            continue

        # 2. Deduplication
        ref = normalized_row["settlement_reference"]
        if ref in seen_in_file:
            duplicate_count += 1
            errors.append(
                RowError(
                    row_number=idx,
                    field="settlement_reference",
                    error=f"Duplicate settlement reference '{ref}' found within the uploaded file.",
                    raw_value=ref,
                )
            )
            continue

        if ref in existing_refs:
            duplicate_count += 1
            errors.append(
                RowError(
                    row_number=idx,
                    field="settlement_reference",
                    error=f"Settlement reference '{ref}' already exists in database.",
                    raw_value=ref,
                )
            )
            continue

        seen_in_file.add(ref)

        settlement = Settlement(
            settlement_reference=ref,
            merchant_id=merchant_id,
            settlement_date=normalized_row["settlement_date"],
            gross_amount=normalized_row["gross_amount"],
            fees=normalized_row["fee_amount"],
            taxes=normalized_row["taxes"],
            refunds=normalized_row["refunds"],
            chargebacks=normalized_row["chargebacks"],
            net_amount=normalized_row["net_amount"],
            status=normalized_row["status"],
        )
        to_insert.append(settlement)

    if to_insert:
        db.add_all(to_insert)

    return len(to_insert), duplicate_count, invalid_count, errors
