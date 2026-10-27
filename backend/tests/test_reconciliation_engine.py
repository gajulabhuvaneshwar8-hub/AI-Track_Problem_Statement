"""
tests/test_reconciliation_engine.py

Unit tests for the deterministic reconciliation engine:
- Level 1: Exact reference matching
- Level 2: Normalized reference matching
- Level 3: Amount + Date fallback matching (single candidate vs multiple candidates)
- Amount mismatch detection
- Missing in bank & Missing in gateway detection
- Duplicate detection
- Settlement delay calculation (mild vs severe delay)
- Gateway success vs Bank failure status conflict
- Confidence score boundaries
"""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from app.models.bank_transaction import BankTransaction
from app.models.enums import MatchStatus, TransactionSource, TransactionStatus
from app.models.transaction import Transaction
from app.services.reconciliation.confidence import calculate_confidence
from app.services.reconciliation.duplicate_detector import normalize_reference
from app.services.reconciliation.reconciliation_engine import ReconciliationEngine


def _make_gtxn(
    ref: str,
    amount: str = "1000.00",
    date: str = "2026-09-01 10:00:00",
    status: TransactionStatus = TransactionStatus.success,
    currency: str = "USD",
) -> Transaction:
    """Helper to build an in-memory Transaction instance."""
    dt = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    return Transaction(
        id=uuid.uuid4(),
        transaction_reference=ref,
        amount=Decimal(amount),
        currency=currency,
        transaction_date=dt,
        status=status,
        source=TransactionSource.gateway,
    )


def _make_btxn(
    bank_ref: str,
    txn_ref: str = None,
    amount: str = "1000.00",
    date: str = "2026-09-01 10:00:00",
    status: str = "posted",
) -> BankTransaction:
    """Helper to build an in-memory BankTransaction instance."""
    dt = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    return BankTransaction(
        id=uuid.uuid4(),
        bank_reference=bank_ref,
        transaction_reference=txn_ref,
        amount=Decimal(amount),
        transaction_date=dt,
        status=status,
    )


class TestReconciliationEngineUnits:
    """Pure unit tests for ReconciliationEngine and its matching hierarchy."""

    def test_exact_reference_match(self):
        engine = ReconciliationEngine()
        gtxn = _make_gtxn("TXN001", amount="1000.00")
        btxn = _make_btxn("BNK001", txn_ref="TXN001", amount="1000.00")

        candidates = engine.reconcile([gtxn], [btxn])
        assert len(candidates) == 1
        cand = candidates[0]
        assert cand.match_status == MatchStatus.matched
        assert cand.matching_method == "exact_reference"
        assert cand.confidence_score == Decimal("1.0000")
        assert cand.difference_amount == Decimal("0.0000")

    def test_normalized_reference_match(self):
        engine = ReconciliationEngine()
        gtxn = _make_gtxn("txn-005", amount="500.00")
        btxn = _make_btxn("BNK005", txn_ref="TXN005", amount="500.00")

        candidates = engine.reconcile([gtxn], [btxn])
        assert len(candidates) == 1
        cand = candidates[0]
        assert cand.match_status == MatchStatus.matched
        assert cand.matching_method == "normalized_reference"
        assert cand.confidence_score == Decimal("0.9500")

    def test_amount_mismatch(self):
        engine = ReconciliationEngine()
        gtxn = _make_gtxn("TXN002", amount="2500.00")
        btxn = _make_btxn("BNK002", txn_ref="TXN002", amount="2400.00")

        candidates = engine.reconcile([gtxn], [btxn])
        assert len(candidates) == 1
        cand = candidates[0]
        assert cand.match_status == MatchStatus.amount_mismatch
        assert cand.expected_amount == Decimal("2500.00")
        assert cand.actual_amount == Decimal("2400.00")
        assert cand.difference_amount == Decimal("-100.00")
        assert cand.confidence_score == Decimal("0.9000")
        assert "-100.00" in cand.explanation

    def test_missing_in_bank(self):
        engine = ReconciliationEngine()
        gtxn = _make_gtxn("TXN003", amount="5000.00")

        candidates = engine.reconcile([gtxn], [])
        assert len(candidates) == 1
        cand = candidates[0]
        assert cand.match_status == MatchStatus.missing_in_bank
        assert cand.expected_amount == Decimal("5000.00")
        assert cand.actual_amount == Decimal("0.0000")
        assert cand.difference_amount == Decimal("-5000.00")
        assert cand.confidence_score == Decimal("0.0000")
        assert cand.matching_method == "no_bank_match"

    def test_missing_in_gateway(self):
        engine = ReconciliationEngine()
        btxn = _make_btxn("BNK004", amount="3000.00")

        candidates = engine.reconcile([], [btxn])
        assert len(candidates) == 1
        cand = candidates[0]
        assert cand.match_status == MatchStatus.missing_in_gateway
        assert cand.expected_amount == Decimal("0.0000")
        assert cand.actual_amount == Decimal("3000.00")
        assert cand.difference_amount == Decimal("3000.00")
        assert cand.confidence_score == Decimal("0.0000")
        assert cand.matching_method == "no_gateway_match"

    def test_gateway_duplicate_detected(self):
        engine = ReconciliationEngine()
        gtxn1 = _make_gtxn("TXN-DUP-01", amount="100.00")
        gtxn2 = _make_gtxn("TXN-DUP-01", amount="100.00")

        candidates = engine.reconcile([gtxn1, gtxn2], [])
        dup_cands = [c for c in candidates if c.match_status == MatchStatus.duplicate]
        assert len(dup_cands) >= 1
        assert dup_cands[0].confidence_score == Decimal("0.0000")

    def test_delayed_transaction(self):
        engine = ReconciliationEngine(delay_threshold_days=1, severe_delay_threshold_days=3)
        gtxn = _make_gtxn("TXN-DEL-01", amount="150.00", date="2026-09-01 10:00:00")
        # 2 days delay: > 1 day threshold, but <= 3 days severe threshold
        btxn = _make_btxn("BNK-DEL-01", txn_ref="TXN-DEL-01", amount="150.00", date="2026-09-03 12:00:00")

        candidates = engine.reconcile([gtxn], [btxn])
        assert len(candidates) == 1
        cand = candidates[0]
        assert cand.match_status == MatchStatus.matched
        assert cand.is_delayed is True
        assert cand.is_severely_delayed is False
        assert cand.matching_method == "exact_reference_delayed"
        assert cand.confidence_score == Decimal("0.8500")

    def test_severe_settlement_delay(self):
        engine = ReconciliationEngine(delay_threshold_days=1, severe_delay_threshold_days=3)
        gtxn = _make_gtxn("TXN-SEV-01", amount="150.00", date="2026-09-01 10:00:00")
        # 5 days delay: > 3 days severe threshold
        btxn = _make_btxn("BNK-SEV-01", txn_ref="TXN-SEV-01", amount="150.00", date="2026-09-06 10:00:00")

        candidates = engine.reconcile([gtxn], [btxn])
        assert len(candidates) == 1
        cand = candidates[0]
        assert cand.match_status == MatchStatus.matched
        assert cand.is_delayed is True
        assert cand.is_severely_delayed is True

    def test_status_mismatch_gateway_success_bank_failed(self):
        engine = ReconciliationEngine()
        gtxn = _make_gtxn("TXN-FAIL-01", amount="200.00", status=TransactionStatus.success)
        btxn = _make_btxn("BNK-FAIL-01", txn_ref="TXN-FAIL-01", amount="200.00", status="failed")

        candidates = engine.reconcile([gtxn], [btxn])
        assert len(candidates) == 1
        cand = candidates[0]
        assert cand.match_status == MatchStatus.unresolved
        assert cand.has_status_mismatch is True
        assert "failure" in cand.explanation

    def test_amount_date_fallback_single_candidate(self):
        engine = ReconciliationEngine(date_tolerance_days=1)
        gtxn = _make_gtxn("TXN-FB-01", amount="750.00", date="2026-09-01 12:00:00")
        # No matching reference, but same amount and next day
        btxn = _make_btxn("BNK-OTHER-REF", txn_ref=None, amount="750.00", date="2026-09-02 08:00:00")

        candidates = engine.reconcile([gtxn], [btxn])
        assert len(candidates) == 1
        cand = candidates[0]
        assert cand.match_status == MatchStatus.matched
        assert cand.matching_method == "amount_date_fallback"
        assert cand.confidence_score == Decimal("0.8000")

    def test_amount_date_fallback_multiple_candidates_unresolved(self):
        engine = ReconciliationEngine(date_tolerance_days=1)
        gtxn = _make_gtxn("TXN-MULTI-01", amount="800.00", date="2026-09-01 12:00:00")
        # Two bank records with same amount and date
        btxn1 = _make_btxn("BNK-AMBIG-01", txn_ref=None, amount="800.00", date="2026-09-01 14:00:00")
        btxn2 = _make_btxn("BNK-AMBIG-02", txn_ref=None, amount="800.00", date="2026-09-02 10:00:00")

        candidates = engine.reconcile([gtxn], [btxn1, btxn2])
        # Gateway transaction should be marked unresolved
        gtxn_cands = [c for c in candidates if c.transaction and c.transaction.id == gtxn.id]
        assert len(gtxn_cands) == 1
        assert gtxn_cands[0].match_status == MatchStatus.unresolved
        assert gtxn_cands[0].confidence_score == Decimal("0.3000")
        assert "Multiple" in gtxn_cands[0].explanation

    def test_normalize_reference_helper(self):
        assert normalize_reference("TXN-001") == "TXN001"
        assert normalize_reference(" txn_001 ") == "TXN001"
        assert normalize_reference("PAY-REC#99") == "PAYREC99"
        assert normalize_reference("") == ""
