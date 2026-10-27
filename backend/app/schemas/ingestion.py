"""
app/schemas/ingestion.py

Pydantic schemas for file upload, ingestion results, and batch history.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ImportSource, ImportStatus


class RowError(BaseModel):
    """Details for a rejected or invalid row during file ingestion."""

    row_number: int = Field(..., description="1-based row index in file")
    field: Optional[str] = Field(None, description="Field or column causing failure")
    error: str = Field(..., description="Error message describing why row was rejected")
    raw_value: Optional[Any] = Field(None, description="Original value in file")


class ImportResultResponse(BaseModel):
    """Summary response returned immediately after file ingestion."""

    batch_id: uuid.UUID
    file_name: str
    file_type: str
    source: ImportSource
    merchant_id: Optional[uuid.UUID] = None
    total_rows: int
    imported_rows: int
    duplicate_rows: int
    invalid_rows: int
    status: ImportStatus
    errors: List[RowError] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImportBatchResponse(BaseModel):
    """Schema for querying import batch history."""

    id: uuid.UUID
    merchant_id: Optional[uuid.UUID] = None
    file_name: str
    file_type: str
    source: ImportSource
    total_rows: int
    imported_rows: int
    duplicate_rows: int
    invalid_rows: int
    status: ImportStatus
    error_details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
