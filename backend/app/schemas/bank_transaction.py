"""
app/schemas/bank_transaction.py

Pydantic schemas for bank statement transactions.
Monetary amounts use Decimal — never float.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import PaginatedResponse


class BankTransactionCreate(BaseModel):
    bank_reference: str = Field(..., max_length=100, examples=["BNK-20240101-0042"])
    transaction_reference: Optional[str] = Field(None, max_length=100)
    amount: Decimal = Field(..., gt=0, decimal_places=4, examples=["1250.00"])
    transaction_date: datetime
    description: Optional[str] = Field(None, examples=["PAYMENT REF TXN-001"])
    bank_name: Optional[str] = Field(None, max_length=100, examples=["HSBC"])
    status: Optional[str] = Field(None, max_length=50, examples=["posted"])

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("amount must be greater than zero")
        return v


class BankTransactionUpdate(BaseModel):
    transaction_reference: Optional[str] = Field(None, max_length=100)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=4)
    transaction_date: Optional[datetime] = None
    description: Optional[str] = None
    bank_name: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)


class BankTransactionResponse(BaseModel):
    id: uuid.UUID
    bank_reference: str
    transaction_reference: Optional[str]
    amount: Decimal
    transaction_date: datetime
    description: Optional[str]
    bank_name: Optional[str]
    status: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


PaginatedBankTransactions = PaginatedResponse[BankTransactionResponse]
