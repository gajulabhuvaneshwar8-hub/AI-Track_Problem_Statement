"""
app/services/ingestion package.

Provides CSV/Excel parsing, normalization, validation, and database ingestion
for payment gateway, bank, and settlement files.
"""

from app.services.ingestion.bank_importer import import_bank_dataframe
from app.services.ingestion.csv_reader import CSVReadError, read_csv_bytes
from app.services.ingestion.excel_reader import ExcelReadError, read_excel_bytes
from app.services.ingestion.gateway_importer import import_gateway_dataframe
from app.services.ingestion.import_service import ImportService, IngestionError
from app.services.ingestion.normalizer import (
    BANK_ALIASES,
    GATEWAY_ALIASES,
    SETTLEMENT_ALIASES,
    map_columns,
    normalize_bank_status,
    normalize_currency,
    normalize_gateway_status,
    normalize_settlement_status,
    parse_datetime,
    parse_decimal,
)
from app.services.ingestion.settlement_importer import import_settlement_dataframe
from app.services.ingestion.validators import (
    validate_bank_row,
    validate_gateway_row,
    validate_settlement_row,
)

__all__ = [
    "ImportService",
    "IngestionError",
    "read_csv_bytes",
    "CSVReadError",
    "read_excel_bytes",
    "ExcelReadError",
    "import_gateway_dataframe",
    "import_bank_dataframe",
    "import_settlement_dataframe",
    "map_columns",
    "parse_decimal",
    "parse_datetime",
    "normalize_currency",
    "normalize_gateway_status",
    "normalize_bank_status",
    "normalize_settlement_status",
    "validate_gateway_row",
    "validate_bank_row",
    "validate_settlement_row",
    "GATEWAY_ALIASES",
    "BANK_ALIASES",
    "SETTLEMENT_ALIASES",
]
