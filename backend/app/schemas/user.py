"""
app/schemas/user.py

Pydantic schemas for user authentication and management.
Passwords are NEVER returned in any response schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class UserCreate(BaseModel):
    """Payload for registering a new user."""

    name: str = Field(..., min_length=1, max_length=255, examples=["Alice Smith"])
    email: EmailStr = Field(..., examples=["alice@example.com"])
    password: str = Field(..., min_length=8, examples=["S3cur3P@ss"])
    role: UserRole = Field(default=UserRole.finance_user)

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name must not be blank")
        return v.strip()


class UserLogin(BaseModel):
    """Payload for authenticating a user."""

    email: EmailStr = Field(..., examples=["alice@example.com"])
    password: str = Field(..., min_length=1, examples=["S3cur3P@ss"])


# ---------------------------------------------------------------------------
# Response schemas  (password_hash is NEVER included)
# ---------------------------------------------------------------------------


class UserResponse(BaseModel):
    """Safe public view of a user record."""

    id: uuid.UUID
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Token schemas
# ---------------------------------------------------------------------------


class Token(BaseModel):
    """Bare JWT token envelope."""

    access_token: str
    token_type: str = "bearer"


class TokenWithUser(Token):
    """JWT token envelope with embedded user info."""

    user: UserResponse
