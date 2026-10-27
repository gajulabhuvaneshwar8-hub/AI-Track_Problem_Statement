"""
app/services/ingestion/csv_reader.py

CSV file parser for financial file uploads.
Reads CSV bytes into a pandas DataFrame with validation on encoding and headers.
"""

import io
from typing import List

import pandas as pd


class CSVReadError(Exception):
    """Raised when CSV cannot be parsed or is empty/invalid."""
    pass


def read_csv_bytes(file_bytes: bytes) -> pd.DataFrame:
    """
    Parse raw CSV bytes into a sanitized pandas DataFrame.
    Tries utf-8, utf-8-sig (BOM), and latin1 encodings.
    Strips column whitespace and converts empty strings to NaN.
    """
    if not file_bytes or len(file_bytes.strip()) == 0:
        raise CSVReadError("Uploaded CSV file is empty.")

    encodings = ["utf-8-sig", "utf-8", "latin1"]
    df = None

    for enc in encodings:
        try:
            df = pd.read_csv(
                io.BytesIO(file_bytes),
                encoding=enc,
                dtype=str,  # Read all columns as str to avoid losing formatting
                skipinitialspace=True,
            )
            break
        except Exception:
            continue

    if df is None:
        raise CSVReadError("Unable to decode CSV file. Supported encodings: UTF-8, Latin-1.")

    if df.empty:
        raise CSVReadError("CSV file contains no data rows.")

    # Clean whitespace and BOM in column names
    df.columns = [str(col).strip().lstrip("\ufeff") for col in df.columns]


    # Drop fully empty rows
    df = df.dropna(how="all")

    if df.empty:
        raise CSVReadError("CSV file contains no non-empty rows.")

    return df
