"""
app/services/merchant_service.py

Database operations for the Merchant entity.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantUpdate

logger = logging.getLogger(__name__)


def create_merchant(db: Session, payload: MerchantCreate) -> Merchant:
    """Create and persist a new Merchant. Raises ValueError on duplicate email."""
    existing = db.query(Merchant).filter(Merchant.email == payload.email.lower()).first()
    if existing:
        raise ValueError(f"Email '{payload.email}' is already registered to a merchant")

    merchant = Merchant(
        id=uuid.uuid4(),
        name=payload.name,
        email=payload.email.lower(),
        business_name=payload.business_name,
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    logger.info("Created merchant %s", merchant.id)
    return merchant


def get_merchant(db: Session, merchant_id: uuid.UUID) -> Optional[Merchant]:
    """Return a Merchant by primary key, or None."""
    return db.get(Merchant, merchant_id)


def list_merchants(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
) -> Tuple[List[Merchant], int]:
    """Return (items, total_count) with optional pagination."""
    query = db.query(Merchant)
    total = query.count()
    items = query.order_by(Merchant.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def update_merchant(
    db: Session,
    merchant_id: uuid.UUID,
    payload: MerchantUpdate,
) -> Optional[Merchant]:
    """Partially update a Merchant. Returns None if not found."""
    merchant = get_merchant(db, merchant_id)
    if not merchant:
        return None

    updates = payload.model_dump(exclude_unset=True)
    if "email" in updates:
        updates["email"] = updates["email"].lower()
    for field, value in updates.items():
        setattr(merchant, field, value)

    db.commit()
    db.refresh(merchant)
    return merchant


def delete_merchant(db: Session, merchant_id: uuid.UUID) -> bool:
    """Delete a Merchant. Returns True if deleted, False if not found."""
    merchant = get_merchant(db, merchant_id)
    if not merchant:
        return False
    db.delete(merchant)
    db.commit()
    return True
