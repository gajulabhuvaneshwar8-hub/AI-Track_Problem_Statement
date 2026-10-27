"""
app/models/__init__.py

Import all ORM models so that:
  1. SQLAlchemy's mapper registry is fully populated at application start.
  2. Alembic autogenerate can detect all tables for migration generation.

Import order respects FK dependencies:
  - Enums (no deps)
  - User, Merchant (leaf tables)
  - Transaction, BankTransaction, Settlement (depend on Merchant / User)
  - ReconciliationResult (depends on Transaction + BankTransaction)
  - PaymentException (depends on ReconciliationResult + User)
  - AuditLog (depends on User)
"""

# Enums — must come first so models can import from here
from app.models.enums import (  # noqa: F401
    AgentDecision,
    AnalysisStatus,
    AnalysisType,
    BankTransactionStatus,
    EscalationTeam,
    ExceptionSeverity,
    ExceptionStatus,
    ImportSource,
    ImportStatus,
    InvestigationStatus,
    MatchStatus,
    RiskLevel,
    SettlementStatus,
    TransactionSource,
    TransactionStatus,
    UserRole,
)

# Models — import in dependency order
from app.models.user import User  # noqa: F401
from app.models.merchant import Merchant  # noqa: F401
from app.models.transaction import Transaction  # noqa: F401
from app.models.bank_transaction import BankTransaction  # noqa: F401
from app.models.settlement import Settlement  # noqa: F401
from app.models.reconciliation_result import ReconciliationResult  # noqa: F401
from app.models.exception import PaymentException  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.import_batch import ImportBatch  # noqa: F401
from app.models.ai_analysis import AIAnalysis  # noqa: F401
from app.models.agent_investigation import AgentInvestigation  # noqa: F401

__all__ = [
    # Enums
    "UserRole",
    "TransactionStatus",
    "TransactionSource",
    "BankTransactionStatus",
    "SettlementStatus",
    "MatchStatus",
    "ExceptionSeverity",
    "ExceptionStatus",
    "ImportStatus",
    "ImportSource",
    "AnalysisType",
    "RiskLevel",
    "AnalysisStatus",
    "InvestigationStatus",
    "AgentDecision",
    "EscalationTeam",
    # Models
    "User",
    "Merchant",
    "Transaction",
    "BankTransaction",
    "Settlement",
    "ReconciliationResult",
    "PaymentException",
    "AuditLog",
    "ImportBatch",
    "AIAnalysis",
    "AgentInvestigation",
]


