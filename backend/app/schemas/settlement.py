"""
app/schemas/settlement.py

Pydantic schemas for settlement batches.
All monetary amounts use Decimal — never float.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.enums import SettlementStatus


class SettlementCreate(BaseModel):
    settlement_reference: str = Field(..., max_length=100, examples=["SET-20240101-001"])
    merchant_id: Optional[uuid.UUID] = None
    settlement_date: datetime
    gross_amount: Decimal = Field(..., gt=0, decimal_places=4, examples=["10000.00"])
    fees: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)
    taxes: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)
    refunds: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)
    chargebacks: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=4)
    net_amount: Decimal = Field(..., decimal_places=4, examples=["9550.00"])
    status: Optional[SettlementStatus] = SettlementStatus.pending

    @field_validator("gross_amount")
    @classmethod
    def gross_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("gross_amount must be greater than zero")
        return v


class SettlementResponse(BaseModel):
    id: uuid.UUID
    settlement_reference: str
    merchant_id: Optional[uuid.UUID]
    settlement_date: datetime
    gross_amount: Decimal
    fees: Decimal
    taxes: Decimal
    refunds: Decimal
    chargebacks: Decimal
    net_amount: Decimal
    status: Optional[SettlementStatus]
    created_at: datetime

    model_config = {"from_attributes": True}
