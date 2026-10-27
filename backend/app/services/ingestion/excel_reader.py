"""
app/services/ingestion/excel_reader.py

Excel (.xlsx, .xls) file parser for financial file uploads.
Uses openpyxl for .xlsx and xlrd for .xls.
"""

import io
import pandas as pd


class ExcelReadError(Exception):
    """Raised when Excel file cannot be parsed or is empty/invalid."""
    pass


def read_excel_bytes(file_bytes: bytes, file_ext: str = "xlsx") -> pd.DataFrame:
    """
    Parse Excel file bytes into a sanitized pandas DataFrame.
    """
    if not file_bytes or len(file_bytes) == 0:
        raise ExcelReadError("Uploaded Excel file is empty.")

    engine = "openpyxl" if file_ext.lower().endswith("xlsx") else "xlrd"

    try:
        df = pd.read_excel(
            io.BytesIO(file_bytes),
            engine=engine,
            dtype=str,
        )
    except Exception as e:
        raise ExcelReadError(f"Failed to read Excel file: {str(e)}")

    if df.empty:
        raise ExcelReadError("Excel file contains no data rows.")

    # Clean whitespace in column names
    df.columns = [str(col).strip() for col in df.columns]

    # Drop fully empty rows
    df = df.dropna(how="all")

    if df.empty:
        raise ExcelReadError("Excel file contains no non-empty rows.")

    return df
