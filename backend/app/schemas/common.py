"""
app/schemas/common.py

Shared schema primitives reused across all domain schemas.
"""

from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated list response envelope."""

    items: List[T]
    page: int
    page_size: int
    total: int

    model_config = {"from_attributes": True}
