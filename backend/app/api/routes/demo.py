"""
app/api/routes/demo.py

Development / Demonstration helper endpoint to load synthetic sample datasets.
Restricted to authenticated administrators for demonstration and testing purposes.
"""

from __future__ import annotations

import logging
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, require_admin
from app.models.enums import ImportSource
from app.models.merchant import Merchant
from app.models.user import User
from app.services.ingestion.import_service import ImportService
from app.services.merchant_service import create_merchant
from app.schemas.merchant import MerchantCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/demo", tags=["Demo Helper"])


def _find_sample_dir() -> Path:
    """Resolve the data/sample directory reliably."""
    # Try relative to repo root or backend parent
    candidates = [
        Path("data/sample"),
        Path("../data/sample"),
        Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "sample",
    ]
    for p in candidates:
        if p.exists() and p.is_dir():
            return p.resolve()
    # Fallback to current working directory / data / sample
    return Path("data/sample").resolve()


@router.post(
    "/load-sample-data",
    summary="[Demo Only] Load synthetic gateway, bank, and settlement sample datasets",
    status_code=status.HTTP_200_OK,
)
def load_sample_data(
    merchant_id: Optional[uuid.UUID] = Query(
        None, description="Optional target merchant ID. If omitted, uses default demo merchant."
    ),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db_session),
) -> dict:
    """
    Idempotently loads synthetic sample datasets from `data/sample/`:
    - gateway_transactions.csv
    - bank_transactions.csv
    - settlements.csv

    Requirements:
    - Authenticated administrator only.
    - Idempotent: repeated runs safely skip already imported records without duplication.
    """
    logger.info("Demo sample data load triggered by admin user=%s", current_user.email)

    # 1. Resolve or initialize demo merchant
    target_merchant: Optional[Merchant] = None
    if merchant_id:
        target_merchant = db.get(Merchant, merchant_id)
        if not target_merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Merchant '{merchant_id}' not found.",
            )
    else:
        # Pick the first available merchant or create a default demo merchant
        target_merchant = db.query(Merchant).first()
        if not target_merchant:
            target_merchant = create_merchant(
                db,
                MerchantCreate(
                    name="Demo Merchant Enterprise",
                    email="demo.merchant@example.com",
                    business_name="Demo Merchant Enterprise Inc.",
                ),
            )

    sample_dir = _find_sample_dir()
    gw_file = sample_dir / "gateway_transactions.csv"
    bank_file = sample_dir / "bank_transactions.csv"
    settl_file = sample_dir / "settlements.csv"

    if not gw_file.exists() or not bank_file.exists() or not settl_file.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sample data files not found in resolved directory: {sample_dir}",
        )

    try:
        gw_bytes = gw_file.read_bytes()
        bank_bytes = bank_file.read_bytes()
        settl_bytes = settl_file.read_bytes()

        gw_res = ImportService.ingest_file(
            file_bytes=gw_bytes,
            file_name="gateway_transactions.csv",
            source=ImportSource.gateway,
            merchant_id=target_merchant.id,
            db=db,
        )

        bank_res = ImportService.ingest_file(
            file_bytes=bank_bytes,
            file_name="bank_transactions.csv",
            source=ImportSource.bank,
            merchant_id=target_merchant.id,
            db=db,
        )

        settl_res = ImportService.ingest_file(
            file_bytes=settl_bytes,
            file_name="settlements.csv",
            source=ImportSource.settlement,
            merchant_id=target_merchant.id,
            db=db,
        )

        return {
            "status": "success",
            "message": "Demo sample datasets processed successfully (idempotent)",
            "merchant_id": str(target_merchant.id),
            "merchant_name": target_merchant.name,
            "gateway": {
                "imported": gw_res.imported_rows,
                "duplicates": gw_res.duplicate_rows,
                "failed": gw_res.invalid_rows,
            },
            "bank": {
                "imported": bank_res.imported_rows,
                "duplicates": bank_res.duplicate_rows,
                "failed": bank_res.invalid_rows,
            },
            "settlement": {
                "imported": settl_res.imported_rows,
                "duplicates": settl_res.duplicate_rows,
                "failed": settl_res.invalid_rows,
            },
        }
    except Exception as e:
        logger.exception("Failed to load demo sample data: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest sample demo files.",
        )
