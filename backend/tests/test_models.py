"""
tests/test_models.py

Basic ORM model tests — verifies:
  1. All models import without error.
  2. SQLAlchemy tables are created correctly (via conftest engine fixture).
  3. CRUD round-trips for each model work correctly.
  4. Foreign-key relationships resolve correctly.
  5. Decimal (Numeric) money values survive a DB round-trip as Decimal, not float.
  6. Enum columns accept valid values and store them correctly.

All tests use SQLite in-memory (no Postgres required).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest

# ---------------------------------------------------------------------------
# 1. Import verification — if any model fails to import the test collection
#    itself fails, which is the desired behaviour.
# ---------------------------------------------------------------------------
from app.models import (
    AuditLog,
    BankTransaction,
    Merchant,
    PaymentException,
    ReconciliationResult,
    Settlement,
    Transaction,
    User,
)
from app.models.enums import (
    ExceptionSeverity,
    ExceptionStatus,
    MatchStatus,
    SettlementStatus,
    TransactionSource,
    TransactionStatus,
    UserRole,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_user(role: UserRole = UserRole.finance_user) -> User:
    return User(
        id=uuid.uuid4(),
        name="Test User",
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_password_value",
        role=role,
        is_active=True,
    )


def _make_merchant() -> Merchant:
    return Merchant(
        id=uuid.uuid4(),
        name="Acme Corp",
        email=f"merchant_{uuid.uuid4().hex[:8]}@acme.com",
        business_name="Acme Corporation",
    )


# ---------------------------------------------------------------------------
# 2. Schema creation — tables must exist after fixture setup
# ---------------------------------------------------------------------------

class TestSchemaCreation:
    def test_all_tables_exist(self, engine):
        """All 8 model tables must be present in the metadata."""
        from sqlalchemy import inspect as sa_inspect

        inspector = sa_inspect(engine)
        table_names = set(inspector.get_table_names())

        expected = {
            "users",
            "merchants",
            "transactions",
            "bank_transactions",
            "settlements",
            "reconciliation_results",
            "exceptions",
            "audit_logs",
        }
        assert expected.issubset(table_names), (
            f"Missing tables: {expected - table_names}"
        )


# ---------------------------------------------------------------------------
# 3. User model
# ---------------------------------------------------------------------------

class TestUserModel:
    def test_create_admin_user(self, session):
        user = _make_user(role=UserRole.admin)
        session.add(user)
        session.flush()

        fetched = session.get(User, user.id)
        assert fetched is not None
        assert fetched.email == user.email
        assert fetched.role == UserRole.admin
        assert fetched.is_active is True

    def test_create_finance_user(self, session):
        user = _make_user(role=UserRole.finance_user)
        session.add(user)
        session.flush()

        fetched = session.get(User, user.id)
        assert fetched.role == UserRole.finance_user

    def test_user_email_is_unique(self, session):
        """Inserting two users with the same email must raise an integrity error."""
        from sqlalchemy.exc import IntegrityError

        email = f"dup_{uuid.uuid4().hex[:6]}@example.com"
        u1 = User(id=uuid.uuid4(), name="A", email=email, password_hash="x", role=UserRole.finance_user)
        u2 = User(id=uuid.uuid4(), name="B", email=email, password_hash="y", role=UserRole.finance_user)
        session.add(u1)
        session.flush()
        session.add(u2)
        with pytest.raises(IntegrityError):
            session.flush()


# ---------------------------------------------------------------------------
# 4. Merchant model
# ---------------------------------------------------------------------------

class TestMerchantModel:
    def test_create_merchant(self, session):
        m = _make_merchant()
        session.add(m)
        session.flush()

        fetched = session.get(Merchant, m.id)
        assert fetched is not None
        assert fetched.business_name == "Acme Corporation"

    def test_merchant_email_unique(self, session):
        from sqlalchemy.exc import IntegrityError

        email = f"m_{uuid.uuid4().hex[:6]}@acme.com"
        m1 = Merchant(id=uuid.uuid4(), name="X", email=email)
        m2 = Merchant(id=uuid.uuid4(), name="Y", email=email)
        session.add(m1)
        session.flush()
        session.add(m2)
        with pytest.raises(IntegrityError):
            session.flush()


# ---------------------------------------------------------------------------
# 5. Transaction model — Decimal money + enums
# ---------------------------------------------------------------------------

class TestTransactionModel:
    def test_create_transaction_with_decimal_amount(self, session):
        """Amount must survive the DB round-trip as Decimal, not float."""
        merchant = _make_merchant()
        session.add(merchant)
        session.flush()

        txn = Transaction(
            id=uuid.uuid4(),
            transaction_reference=f"TXN-{uuid.uuid4().hex[:10]}",
            merchant_id=merchant.id,
            amount=Decimal("1234.5678"),
            currency="USD",
            transaction_date=_now(),
            status=TransactionStatus.success,
            source=TransactionSource.gateway,
        )
        session.add(txn)
        session.flush()

        fetched = session.get(Transaction, txn.id)
        assert fetched is not None
        assert isinstance(fetched.amount, Decimal), (
            f"Expected Decimal, got {type(fetched.amount)}"
        )
        assert fetched.amount == Decimal("1234.5678")
        assert fetched.status == TransactionStatus.success
        assert fetched.source == TransactionSource.gateway

    def test_transaction_reference_unique(self, session):
        from sqlalchemy.exc import IntegrityError

        ref = f"TXN-{uuid.uuid4().hex[:10]}"
        t1 = Transaction(id=uuid.uuid4(), transaction_reference=ref, amount=Decimal("10"), transaction_date=_now())
        t2 = Transaction(id=uuid.uuid4(), transaction_reference=ref, amount=Decimal("20"), transaction_date=_now())
        session.add(t1)
        session.flush()
        session.add(t2)
        with pytest.raises(IntegrityError):
            session.flush()

    def test_transaction_merchant_relationship(self, session):
        merchant = _make_merchant()
        session.add(merchant)
        session.flush()

        txn = Transaction(
            id=uuid.uuid4(),
            transaction_reference=f"TXN-{uuid.uuid4().hex[:10]}",
            merchant_id=merchant.id,
            amount=Decimal("99.99"),
            transaction_date=_now(),
        )
        session.add(txn)
        session.flush()
        session.expire_all()

        fetched = session.get(Transaction, txn.id)
        assert fetched.merchant is not None
        assert fetched.merchant.id == merchant.id


# ---------------------------------------------------------------------------
# 6. BankTransaction model — Decimal money
# ---------------------------------------------------------------------------

class TestBankTransactionModel:
    def test_create_bank_transaction(self, session):
        bt = BankTransaction(
            id=uuid.uuid4(),
            bank_reference=f"BNK-{uuid.uuid4().hex[:10]}",
            amount=Decimal("500.0000"),
            transaction_date=_now(),
            bank_name="HSBC",
        )
        session.add(bt)
        session.flush()

        fetched = session.get(BankTransaction, bt.id)
        assert fetched is not None
        assert isinstance(fetched.amount, Decimal)
        assert fetched.amount == Decimal("500.0000")

    def test_bank_reference_unique(self, session):
        from sqlalchemy.exc import IntegrityError

        ref = f"BNK-{uuid.uuid4().hex[:10]}"
        b1 = BankTransaction(id=uuid.uuid4(), bank_reference=ref, amount=Decimal("1"), transaction_date=_now())
        b2 = BankTransaction(id=uuid.uuid4(), bank_reference=ref, amount=Decimal("2"), transaction_date=_now())
        session.add(b1)
        session.flush()
        session.add(b2)
        with pytest.raises(IntegrityError):
            session.flush()


# ---------------------------------------------------------------------------
# 7. Settlement model — all Numeric columns
# ---------------------------------------------------------------------------

class TestSettlementModel:
    def test_create_settlement_with_all_numeric_fields(self, session):
        merchant = _make_merchant()
        session.add(merchant)
        session.flush()

        s = Settlement(
            id=uuid.uuid4(),
            settlement_reference=f"SET-{uuid.uuid4().hex[:10]}",
            merchant_id=merchant.id,
            settlement_date=_now(),
            gross_amount=Decimal("10000.0000"),
            fees=Decimal("250.0000"),
            taxes=Decimal("45.0000"),
            refunds=Decimal("100.0000"),
            chargebacks=Decimal("50.0000"),
            net_amount=Decimal("9555.0000"),
            status=SettlementStatus.settled,
        )
        session.add(s)
        session.flush()

        fetched = session.get(Settlement, s.id)
        assert fetched is not None
        for field in ("gross_amount", "fees", "taxes", "refunds", "chargebacks", "net_amount"):
            val = getattr(fetched, field)
            assert isinstance(val, Decimal), f"{field} should be Decimal, got {type(val)}"
        assert fetched.status == SettlementStatus.settled

    def test_settlement_merchant_relationship(self, session):
        merchant = _make_merchant()
        session.add(merchant)
        session.flush()

        s = Settlement(
            id=uuid.uuid4(),
            settlement_reference=f"SET-{uuid.uuid4().hex[:10]}",
            merchant_id=merchant.id,
            settlement_date=_now(),
            gross_amount=Decimal("1000"),
            net_amount=Decimal("950"),
        )
        session.add(s)
        session.flush()
        session.expire_all()

        fetched = session.get(Settlement, s.id)
        assert fetched.merchant.id == merchant.id


# ---------------------------------------------------------------------------
# 8. ReconciliationResult model — confidence score + match status
# ---------------------------------------------------------------------------

class TestReconciliationResultModel:
    def _setup_txn_and_bank(self, session):
        txn = Transaction(
            id=uuid.uuid4(),
            transaction_reference=f"TXN-{uuid.uuid4().hex[:10]}",
            amount=Decimal("250.00"),
            transaction_date=_now(),
        )
        bt = BankTransaction(
            id=uuid.uuid4(),
            bank_reference=f"BNK-{uuid.uuid4().hex[:10]}",
            amount=Decimal("250.00"),
            transaction_date=_now(),
        )
        session.add_all([txn, bt])
        session.flush()
        return txn, bt

    def test_create_matched_result(self, session):
        txn, bt = self._setup_txn_and_bank(session)

        result = ReconciliationResult(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            bank_transaction_id=bt.id,
            match_status=MatchStatus.matched,
            confidence_score=Decimal("0.9900"),
            expected_amount=Decimal("250.00"),
            actual_amount=Decimal("250.00"),
            difference_amount=Decimal("0.00"),
            matching_method="exact_reference",
            explanation="Transaction reference matched exactly.",
        )
        session.add(result)
        session.flush()

        fetched = session.get(ReconciliationResult, result.id)
        assert fetched is not None
        assert fetched.match_status == MatchStatus.matched
        assert isinstance(fetched.confidence_score, Decimal)
        assert fetched.confidence_score == Decimal("0.9900")
        assert isinstance(fetched.difference_amount, Decimal)

    def test_create_missing_in_bank_result(self, session):
        txn, _ = self._setup_txn_and_bank(session)

        result = ReconciliationResult(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            bank_transaction_id=None,
            match_status=MatchStatus.missing_in_bank,
            confidence_score=Decimal("0.0000"),
        )
        session.add(result)
        session.flush()

        fetched = session.get(ReconciliationResult, result.id)
        assert fetched.bank_transaction_id is None
        assert fetched.match_status == MatchStatus.missing_in_bank

    def test_reconciliation_to_transaction_relationship(self, session):
        txn, bt = self._setup_txn_and_bank(session)

        result = ReconciliationResult(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            bank_transaction_id=bt.id,
            match_status=MatchStatus.matched,
        )
        session.add(result)
        session.flush()
        session.expire_all()

        fetched = session.get(ReconciliationResult, result.id)
        assert fetched.transaction.id == txn.id
        assert fetched.bank_transaction.id == bt.id


# ---------------------------------------------------------------------------
# 9. PaymentException model — severity + status enums, assignee FK
# ---------------------------------------------------------------------------

class TestPaymentExceptionModel:
    def _make_recon_result(self, session) -> ReconciliationResult:
        result = ReconciliationResult(
            id=uuid.uuid4(),
            match_status=MatchStatus.amount_mismatch,
        )
        session.add(result)
        session.flush()
        return result

    def test_create_open_critical_exception(self, session):
        recon = self._make_recon_result(session)

        exc = PaymentException(
            id=uuid.uuid4(),
            reconciliation_id=recon.id,
            severity=ExceptionSeverity.critical,
            category="Amount Mismatch",
            title="Payment amount does not match bank record",
            description="Gateway reported $1000 but bank shows $900.",
            recommended_action="Contact bank to resolve discrepancy.",
            status=ExceptionStatus.open,
        )
        session.add(exc)
        session.flush()

        fetched = session.get(PaymentException, exc.id)
        assert fetched is not None
        assert fetched.severity == ExceptionSeverity.critical
        assert fetched.status == ExceptionStatus.open
        assert fetched.resolved_at is None

    def test_assign_exception_to_user(self, session):
        user = _make_user()
        session.add(user)
        recon = self._make_recon_result(session)
        session.flush()

        exc = PaymentException(
            id=uuid.uuid4(),
            reconciliation_id=recon.id,
            severity=ExceptionSeverity.high,
            title="Duplicate transaction suspected",
            status=ExceptionStatus.investigating,
            assigned_to=user.id,
        )
        session.add(exc)
        session.flush()
        session.expire_all()

        fetched = session.get(PaymentException, exc.id)
        assert fetched.assignee is not None
        assert fetched.assignee.id == user.id

    def test_exception_cascade_from_reconciliation(self, session):
        """Deleting a ReconciliationResult should cascade-delete its exceptions."""
        recon = self._make_recon_result(session)

        exc = PaymentException(
            id=uuid.uuid4(),
            reconciliation_id=recon.id,
            severity=ExceptionSeverity.low,
            title="Minor discrepancy",
            status=ExceptionStatus.open,
        )
        session.add(exc)
        session.flush()
        exc_id = exc.id

        session.delete(recon)
        session.flush()

        # Exception should be gone (cascade delete)
        fetched = session.get(PaymentException, exc_id)
        assert fetched is None


# ---------------------------------------------------------------------------
# 10. AuditLog model — JSON details, nullable user_id
# ---------------------------------------------------------------------------

class TestAuditLogModel:
    def test_create_audit_log_with_user(self, session):
        user = _make_user()
        session.add(user)
        session.flush()

        log = AuditLog(
            id=uuid.uuid4(),
            user_id=user.id,
            action="login",
            entity_type="User",
            entity_id=str(user.id),
            details={"ip": "192.168.1.1", "user_agent": "Mozilla/5.0"},
        )
        session.add(log)
        session.flush()

        fetched = session.get(AuditLog, log.id)
        assert fetched is not None
        assert fetched.action == "login"
        assert fetched.details["ip"] == "192.168.1.1"
        assert fetched.user.id == user.id

    def test_create_system_audit_log_no_user(self, session):
        """System events may be logged without a user_id."""
        log = AuditLog(
            id=uuid.uuid4(),
            user_id=None,
            action="reconciliation_run_started",
            entity_type="ReconciliationRun",
            entity_id="run-001",
            details={"triggered_by": "scheduler"},
        )
        session.add(log)
        session.flush()

        fetched = session.get(AuditLog, log.id)
        assert fetched.user_id is None
        assert fetched.user is None
        assert fetched.details["triggered_by"] == "scheduler"


# ---------------------------------------------------------------------------
# 11. Cross-model relationship chain
# ---------------------------------------------------------------------------

class TestRelationshipChain:
    def test_full_chain(self, session):
        """
        Merchant → Transaction → ReconciliationResult → PaymentException.
        Verify the full FK chain resolves in both directions.
        """
        merchant = _make_merchant()
        user = _make_user(role=UserRole.admin)
        session.add_all([merchant, user])
        session.flush()

        txn = Transaction(
            id=uuid.uuid4(),
            transaction_reference=f"TXN-CHAIN-{uuid.uuid4().hex[:8]}",
            merchant_id=merchant.id,
            amount=Decimal("750.00"),
            currency="GBP",
            transaction_date=_now(),
            status=TransactionStatus.disputed,
            source=TransactionSource.gateway,
        )
        bt = BankTransaction(
            id=uuid.uuid4(),
            bank_reference=f"BNK-CHAIN-{uuid.uuid4().hex[:8]}",
            amount=Decimal("700.00"),
            transaction_date=_now(),
            bank_name="Barclays",
        )
        session.add_all([txn, bt])
        session.flush()

        recon = ReconciliationResult(
            id=uuid.uuid4(),
            transaction_id=txn.id,
            bank_transaction_id=bt.id,
            match_status=MatchStatus.amount_mismatch,
            confidence_score=Decimal("0.4500"),
            expected_amount=txn.amount,
            actual_amount=bt.amount,
            difference_amount=txn.amount - bt.amount,
        )
        session.add(recon)
        session.flush()

        exc = PaymentException(
            id=uuid.uuid4(),
            reconciliation_id=recon.id,
            severity=ExceptionSeverity.high,
            title="Amount mismatch: GBP 50.00 discrepancy",
            status=ExceptionStatus.open,
            assigned_to=user.id,
        )
        log = AuditLog(
            id=uuid.uuid4(),
            user_id=user.id,
            action="exception_created",
            entity_type="PaymentException",
            entity_id=str(exc.id),
        )
        session.add_all([exc, log])
        session.flush()
        session.expire_all()

        # Traverse the full chain
        fetched_exc = session.get(PaymentException, exc.id)
        assert fetched_exc.reconciliation_result.transaction.merchant.id == merchant.id
        assert fetched_exc.assignee.id == user.id
        assert isinstance(fetched_exc.reconciliation_result.difference_amount, Decimal)
        assert fetched_exc.reconciliation_result.difference_amount == Decimal("50.00")
