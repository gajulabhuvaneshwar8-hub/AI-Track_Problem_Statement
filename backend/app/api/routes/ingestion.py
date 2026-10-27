"""
app/api/routes/ingestion.py

API routes for CSV/Excel file uploads and ingestion history.
"""

import os
import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_db_session, require_finance_or_admin
from app.models.enums import ImportSource
from app.models.merchant import Merchant
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.ingestion import ImportBatchResponse, ImportResultResponse
from app.services.ingestion.import_service import ImportService, IngestionError

router = APIRouter(prefix="/ingestion", tags=["Data Ingestion"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


def _validate_uploaded_file(file: UploadFile) -> str:
    """Validate filename extension and return extension."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file has no filename.",
        )
    _, ext = os.path.splitext(file.filename)
    ext_lower = ext.lower()
    if ext_lower not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: .csv, .xlsx, .xls",
        )
    return ext_lower


async def _read_file_content(file: UploadFile) -> bytes:
    """Read file content and enforce size limit."""
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )
    return content


def _verify_merchant(merchant_id: Optional[uuid.UUID], db: Session) -> None:
    """Verify merchant exists if merchant_id is provided."""
    if merchant_id is not None:
        merchant = db.get(Merchant, merchant_id)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Merchant with ID '{merchant_id}' not found.",
            )


@router.post(
    "/gateway",
    response_model=ImportResultResponse,
    summary="Upload and ingest payment gateway transactions file",
)
async def upload_gateway_file(
    file: UploadFile = File(..., description="CSV or Excel gateway transaction export"),
    merchant_id: Optional[uuid.UUID] = Form(None, description="Optional merchant ID associated with transactions"),
    current_user: User = Depends(require_finance_or_admin),
    db: Session = Depends(get_db_session),
) -> ImportResultResponse:
    """
    Ingest payment gateway transactions from CSV/Excel file.
    Validates rows, detects duplicates against existing database records, and stores valid entries.
    """
    _validate_uploaded_file(file)
    _verify_merchant(merchant_id, db)
    content = await _read_file_content(file)

    try:
        result = ImportService.ingest_file(
            file_bytes=content,
            file_name=file.filename or "gateway_upload.csv",
            source=ImportSource.gateway,
            merchant_id=merchant_id,
            db=db,
        )
        return result
    except IngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/bank",
    response_model=ImportResultResponse,
    summary="Upload and ingest bank statement transactions file",
)
async def upload_bank_file(
    file: UploadFile = File(..., description="CSV or Excel bank statement export"),
    merchant_id: Optional[uuid.UUID] = Form(None, description="Optional merchant ID associated with account"),
    current_user: User = Depends(require_finance_or_admin),
    db: Session = Depends(get_db_session),
) -> ImportResultResponse:
    """
    Ingest bank statement transactions from CSV/Excel file.
    Validates rows, detects duplicates against existing database records, and stores valid entries.
    """
    _validate_uploaded_file(file)
    _verify_merchant(merchant_id, db)
    content = await _read_file_content(file)

    try:
        result = ImportService.ingest_file(
            file_bytes=content,
            file_name=file.filename or "bank_upload.csv",
            source=ImportSource.bank,
            merchant_id=merchant_id,
            db=db,
        )
        return result
    except IngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/settlement",
    response_model=ImportResultResponse,
    summary="Upload and ingest settlement batch records file",
)
async def upload_settlement_file(
    file: UploadFile = File(..., description="CSV or Excel processor settlement batch export"),
    merchant_id: Optional[uuid.UUID] = Form(None, description="Optional merchant ID associated with settlement"),
    current_user: User = Depends(require_finance_or_admin),
    db: Session = Depends(get_db_session),
) -> ImportResultResponse:
    """
    Ingest settlement records from CSV/Excel file.
    Validates gross/net/fees, checks duplicates, and stores valid settlement records.
    """
    _validate_uploaded_file(file)
    _verify_merchant(merchant_id, db)
    content = await _read_file_content(file)

    try:
        result = ImportService.ingest_file(
            file_bytes=content,
            file_name=file.filename or "settlement_upload.csv",
            source=ImportSource.settlement,
            merchant_id=merchant_id,
            db=db,
        )
        return result
    except IngestionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/history",
    response_model=PaginatedResponse[ImportBatchResponse],
    summary="Get import batch history",
)
def get_import_history(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    source: Optional[ImportSource] = Query(None, description="Filter by file source"),
    merchant_id: Optional[uuid.UUID] = Query(None, description="Filter by merchant ID"),
    current_user: User = Depends(require_finance_or_admin),
    db: Session = Depends(get_db_session),
) -> PaginatedResponse[ImportBatchResponse]:
    """Retrieve paginated log of all file import batches with stats and errors."""
    batches, total = ImportService.get_batches(
        db=db,
        page=page,
        page_size=page_size,
        source=source,
        merchant_id=merchant_id,
    )

    items = [ImportBatchResponse.model_validate(b) for b in batches]
    return PaginatedResponse[ImportBatchResponse](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )
