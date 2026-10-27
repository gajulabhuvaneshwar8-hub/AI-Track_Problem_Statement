"""
app/schemas/transaction.py

Pydantic schemas for payment transaction CRUD + filtering.
Monetary amounts use Decimal — never float.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.enums import TransactionSource, TransactionStatus
from app.schemas.common import PaginatedResponse


class TransactionCreate(BaseModel):
    transaction_reference: str = Field(..., max_length=100, examples=["TXN-20240101-001"])
    order_reference: Optional[str] = Field(None, max_length=100)
    merchant_id: Optional[uuid.UUID] = None
    customer_reference: Optional[str] = Field(None, max_length=100)
    amount: Decimal = Field(..., gt=0, decimal_places=4, examples=["1250.00"])
    currency: str = Field(default="USD", max_length=3, examples=["USD"])
    transaction_date: datetime
    payment_method: Optional[str] = Field(None, max_length=50, examples=["card"])
    gateway: Optional[str] = Field(None, max_length=100, examples=["Stripe"])
    status: Optional[TransactionStatus] = None
    source: Optional[TransactionSource] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be greater than zero")
        return v

    @field_validator("currency")
    @classmethod
    def currency_upper(cls, v: str) -> str:
        return v.upper()


class TransactionUpdate(BaseModel):
    order_reference: Optional[str] = Field(None, max_length=100)
    customer_reference: Optional[str] = Field(None, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=4)
    currency: Optional[str] = Field(None, max_length=3)
    transaction_date: Optional[datetime] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    gateway: Optional[str] = Field(None, max_length=100)
    status: Optional[TransactionStatus] = None
    source: Optional[TransactionSource] = None


class TransactionResponse(BaseModel):
    id: uuid.UUID
    transaction_reference: str
    order_reference: Optional[str]
    merchant_id: Optional[uuid.UUID]
    customer_reference: Optional[str]
    amount: Decimal
    currency: str
    transaction_date: datetime
    payment_method: Optional[str]
    gateway: Optional[str]
    status: Optional[TransactionStatus]
    source: Optional[TransactionSource]
    created_at: datetime

    model_config = {"from_attributes": True}


PaginatedTransactions = PaginatedResponse[TransactionResponse]
