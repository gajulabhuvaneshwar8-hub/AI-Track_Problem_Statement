"""
app/schemas/merchant.py

Pydantic schemas for merchant CRUD operations.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class MerchantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["Acme Corp"])
    email: EmailStr = Field(..., examples=["payments@acme.com"])
    business_name: Optional[str] = Field(None, max_length=255, examples=["Acme Corporation Ltd."])


class MerchantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    business_name: Optional[str] = Field(None, max_length=255)


class MerchantResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    business_name: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
