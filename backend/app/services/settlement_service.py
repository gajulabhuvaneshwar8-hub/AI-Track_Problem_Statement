"""
app/services/settlement_service.py

Database operations for the Settlement entity.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.settlement import Settlement
from app.schemas.settlement import SettlementCreate

logger = logging.getLogger(__name__)


def create_settlement(db: Session, payload: SettlementCreate) -> Settlement:
    """Create a settlement batch. Raises ValueError on duplicate reference."""
    existing = (
        db.query(Settlement)
        .filter(Settlement.settlement_reference == payload.settlement_reference)
        .first()
    )
    if existing:
        raise ValueError(
            f"settlement_reference '{payload.settlement_reference}' already exists"
        )

    settlement = Settlement(id=uuid.uuid4(), **payload.model_dump())
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    logger.info("Created settlement %s ref=%s", settlement.id, settlement.settlement_reference)
    return settlement


def get_settlement(db: Session, settlement_id: uuid.UUID) -> Optional[Settlement]:
    return db.get(Settlement, settlement_id)


def list_settlements(
    db: Session,
    *,
    merchant_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[Settlement], int]:
    query = db.query(Settlement)
    if merchant_id is not None:
        query = query.filter(Settlement.merchant_id == merchant_id)

    total = query.count()
    items = (
        query.order_by(Settlement.settlement_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items, total
