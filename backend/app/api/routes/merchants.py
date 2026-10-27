"""
app/api/routes/merchants.py

Full CRUD endpoints for the Merchant entity.
All write operations require authentication.
"""

from __future__ import annotations

import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, get_current_user
from app.models.user import User
from app.schemas.merchant import MerchantCreate, MerchantResponse, MerchantUpdate
from app.services import merchant_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.post(
    "",
    response_model=MerchantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new merchant",
)
def create_merchant(
    payload: MerchantCreate,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> MerchantResponse:
    try:
        return merchant_service.create_merchant(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "",
    response_model=List[MerchantResponse],
    summary="List all merchants",
)
def list_merchants(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> List[MerchantResponse]:
    skip = (page - 1) * page_size
    items, _ = merchant_service.list_merchants(db, skip=skip, limit=page_size)
    return items


@router.get(
    "/{merchant_id}",
    response_model=MerchantResponse,
    summary="Get a single merchant by ID",
)
def get_merchant(
    merchant_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> MerchantResponse:
    merchant = merchant_service.get_merchant(db, merchant_id)
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    return merchant


@router.put(
    "/{merchant_id}",
    response_model=MerchantResponse,
    summary="Update a merchant",
)
def update_merchant(
    merchant_id: uuid.UUID,
    payload: MerchantUpdate,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> MerchantResponse:
    merchant = merchant_service.update_merchant(db, merchant_id, payload)
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    return merchant


@router.delete(
    "/{merchant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete a merchant",
)
def delete_merchant(
    merchant_id: uuid.UUID,
    db: Session = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> Response:
    deleted = merchant_service.delete_merchant(db, merchant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
