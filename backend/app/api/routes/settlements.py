"""
app/api/routes/settlements.py

Settlement endpoints: create and read.
Write operations require authentication.
"""

from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_current_user
from app.models.user import User
from app.schemas.settlement import SettlementCreate, SettlementResponse
from app.services import settlement_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settlements", tags=["Settlements"])


@router.post(
    "",
    response_model=SettlementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new settlement batch",
)
def create_settlement(
    payload: SettlementCreate,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> SettlementResponse:
    try:
        return settlement_service.create_settlement(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "",
    response_model=List[SettlementResponse],
    summary="List settlements",
)
def list_settlements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    merchant_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> List[SettlementResponse]:
    skip = (page - 1) * page_size
    items, _ = settlement_service.list_settlements(
        db, merchant_id=merchant_id, skip=skip, limit=page_size
    )
    return items


@router.get(
    "/{settlement_id}",
    response_model=SettlementResponse,
    summary="Get a single settlement by ID",
)
def get_settlement(
    settlement_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> SettlementResponse:
    settlement = settlement_service.get_settlement(db, settlement_id)
    if not settlement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Settlement not found")
    return settlement
