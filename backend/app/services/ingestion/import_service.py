"""
app/services/ingestion/import_service.py

Top-level orchestration service for financial data ingestion.
Coordinates reading, normalization, validation, deduplication, batch tracking,
and database persistence.
"""

import json
import os
import uuid
from typing import List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.enums import ImportSource, ImportStatus
from app.models.import_batch import ImportBatch
from app.schemas.ingestion import ImportResultResponse, RowError
from app.services.ingestion.bank_importer import import_bank_dataframe
from app.services.ingestion.csv_reader import CSVReadError, read_csv_bytes
from app.services.ingestion.excel_reader import ExcelReadError, read_excel_bytes
from app.services.ingestion.gateway_importer import import_gateway_dataframe
from app.services.ingestion.settlement_importer import import_settlement_dataframe


class IngestionError(Exception):
    """General error during ingestion pipeline execution."""
    pass


class ImportService:
    """Manages file ingestion and batch history."""

    @staticmethod
    def ingest_file(
        file_bytes: bytes,
        file_name: str,
        source: ImportSource,
        merchant_id: Optional[uuid.UUID],
        db: Session,
    ) -> ImportResultResponse:
        """
        Execute full ingestion pipeline for an uploaded CSV or Excel file.
        """
        _, ext = os.path.splitext(file_name)
        ext_clean = ext.lower().lstrip(".")

        if ext_clean not in {"csv", "xlsx", "xls"}:
            raise IngestionError(f"Unsupported file format: '.{ext_clean}'. Supported formats: CSV, XLSX, XLS.")

        # 1. Parse into DataFrame
        try:
            if ext_clean == "csv":
                df = read_csv_bytes(file_bytes)
            else:
                df = read_excel_bytes(file_bytes, file_ext=ext_clean)
        except (CSVReadError, ExcelReadError) as e:
            # Create a failed batch record for traceability
            batch = ImportBatch(
                merchant_id=merchant_id,
                file_name=file_name,
                file_type=ext_clean,
                source=source,
                total_rows=0,
                imported_rows=0,
                duplicate_rows=0,
                invalid_rows=0,
                status=ImportStatus.failed,
                error_details=str(e),
            )
            db.add(batch)
            db.commit()
            db.refresh(batch)

            return ImportResultResponse(
                batch_id=batch.id,
                file_name=file_name,
                file_type=ext_clean,
                source=source,
                merchant_id=merchant_id,
                total_rows=0,
                imported_rows=0,
                duplicate_rows=0,
                invalid_rows=0,
                status=ImportStatus.failed,
                errors=[
                    RowError(
                        row_number=1,
                        field="file",
                        error=str(e),
                        raw_value=None,
                    )
                ],
                created_at=batch.created_at,
            )

        total_rows = len(df)

        # 2. Create batch record in 'processing' state
        batch = ImportBatch(
            merchant_id=merchant_id,
            file_name=file_name,
            file_type=ext_clean,
            source=source,
            total_rows=total_rows,
            imported_rows=0,
            duplicate_rows=0,
            invalid_rows=0,
            status=ImportStatus.processing,
        )
        db.add(batch)
        db.flush()

        # 3. Route to importer
        errors: List[RowError] = []
        try:
            if source == ImportSource.gateway:
                imported, duplicates, invalid, errors = import_gateway_dataframe(
                    df, merchant_id, db
                )
            elif source == ImportSource.bank:
                imported, duplicates, invalid, errors = import_bank_dataframe(
                    df, merchant_id, db
                )
            elif source == ImportSource.settlement:
                imported, duplicates, invalid, errors = import_settlement_dataframe(
                    df, merchant_id, db
                )
            else:
                raise IngestionError(f"Unknown import source: {source}")

            # 4. Determine final status
            if imported > 0 and (duplicates == 0 and invalid == 0):
                final_status = ImportStatus.completed
            elif imported > 0:
                final_status = ImportStatus.completed_with_errors
            else:
                final_status = ImportStatus.failed

            batch.imported_rows = imported
            batch.duplicate_rows = duplicates
            batch.invalid_rows = invalid
            batch.status = final_status

            if errors:
                error_summary = [
                    {"row": e.row_number, "field": e.field, "error": e.error}
                    for e in errors[:100]  # Cap stored errors
                ]
                batch.error_details = json.dumps(error_summary)

            db.commit()
            db.refresh(batch)

            return ImportResultResponse(
                batch_id=batch.id,
                file_name=file_name,
                file_type=ext_clean,
                source=source,
                merchant_id=merchant_id,
                total_rows=total_rows,
                imported_rows=imported,
                duplicate_rows=duplicates,
                invalid_rows=invalid,
                status=final_status,
                errors=errors,
                created_at=batch.created_at,
            )

        except Exception as e:
            db.rollback()
            # Mark batch as failed
            failed_batch = ImportBatch(
                merchant_id=merchant_id,
                file_name=file_name,
                file_type=ext_clean,
                source=source,
                total_rows=total_rows,
                imported_rows=0,
                duplicate_rows=0,
                invalid_rows=total_rows,
                status=ImportStatus.failed,
                error_details=str(e),
            )
            db.add(failed_batch)
            db.commit()
            db.refresh(failed_batch)

            return ImportResultResponse(
                batch_id=failed_batch.id,
                file_name=file_name,
                file_type=ext_clean,
                source=source,
                merchant_id=merchant_id,
                total_rows=total_rows,
                imported_rows=0,
                duplicate_rows=0,
                invalid_rows=total_rows,
                status=ImportStatus.failed,
                errors=[
                    RowError(
                        row_number=1,
                        field="system",
                        error=f"Ingestion processing error: {str(e)}",
                        raw_value=None,
                    )
                ],
                created_at=failed_batch.created_at,
            )

    @staticmethod
    def get_batches(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        source: Optional[ImportSource] = None,
        merchant_id: Optional[uuid.UUID] = None,
    ) -> Tuple[List[ImportBatch], int]:
        """Fetch paginated import batch history."""
        stmt = select(ImportBatch)
        count_stmt = select(func.count(ImportBatch.id))

        if source:
            stmt = stmt.where(ImportBatch.source == source)
            count_stmt = count_stmt.where(ImportBatch.source == source)

        if merchant_id:
            stmt = stmt.where(ImportBatch.merchant_id == merchant_id)
            count_stmt = count_stmt.where(ImportBatch.merchant_id == merchant_id)

        total = db.scalar(count_stmt) or 0
        offset = (page - 1) * page_size
        stmt = stmt.order_by(desc(ImportBatch.created_at)).offset(offset).limit(page_size)

        batches = list(db.scalars(stmt).all())
        return batches, total
