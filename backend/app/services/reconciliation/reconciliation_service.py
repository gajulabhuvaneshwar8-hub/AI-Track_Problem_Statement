"""
app/services/reconciliation/reconciliation_service.py

High-level application service for executing reconciliation runs and querying results.
Manages database transactions, idempotency, exception generation, and summary statistics.
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.bank_transaction import BankTransaction
from app.models.enums import ExceptionStatus, MatchStatus
from app.models.exception import PaymentException
from app.models.reconciliation_result import ReconciliationResult
from app.models.transaction import Transaction
from app.schemas.reconciliation import ReconciliationSummaryResponse
from app.services.reconciliation.reconciliation_engine import ReconciliationEngine
from app.services.reconciliation.result_builder import (
    build_exception_for_candidate,
    build_reconciliation_result,
)

logger = logging.getLogger(__name__)


class ReconciliationService:
    """Orchestrates database operations, matching engine execution, and summary reporting."""

    @staticmethod
    def run_reconciliation(
        merchant_id: Optional[uuid.UUID],
        db: Session,
    ) -> ReconciliationSummaryResponse:
        """
        Run the reconciliation engine for a given merchant (or platform-wide).
        Idempotent: updates existing results instead of creating duplicates.
        """
        logger.info("Starting reconciliation run for merchant_id=%s", merchant_id)

        # 1. Fetch Gateway transactions
        gtxn_stmt = select(Transaction)
        if merchant_id:
            gtxn_stmt = gtxn_stmt.where(Transaction.merchant_id == merchant_id)
        gateway_txns = list(db.scalars(gtxn_stmt).all())

        # 2. Fetch Bank transactions
        btxn_stmt = select(BankTransaction)
        bank_txns = list(db.scalars(btxn_stmt).all())

        logger.info(
            "Reconciliation data loaded: %d gateway transactions, %d bank statement records",
            len(gateway_txns),
            len(bank_txns),
        )

        # 3. Run Matching Engine
        engine = ReconciliationEngine()
        candidates = engine.reconcile(gateway_txns, bank_txns)

        # 4. Persist Results & Exceptions with Idempotency
        counts = {
            "matched": 0,
            "partial_match": 0,
            "amount_mismatch": 0,
            "missing_in_bank": 0,
            "missing_in_gateway": 0,
            "duplicate": 0,
            "unresolved": 0,
            "delayed": 0,
        }

        total_expected = Decimal("0.0000")
        total_actual = Decimal("0.0000")
        total_difference = Decimal("0.0000")

        for cand in candidates:
            # Update summary metrics
            st = cand.match_status.value
            if st in counts:
                counts[st] += 1
            if cand.is_delayed:
                counts["delayed"] += 1

            if cand.expected_amount is not None:
                total_expected += cand.expected_amount
            if cand.actual_amount is not None:
                total_actual += cand.actual_amount
            if cand.difference_amount is not None:
                total_difference += cand.difference_amount

            # Check for existing result for idempotency
            existing_result: Optional[ReconciliationResult] = None
            t_id = cand.transaction.id if cand.transaction else None
            b_id = cand.bank_transaction.id if cand.bank_transaction else None

            if t_id and b_id:
                existing_result = db.scalar(
                    select(ReconciliationResult).where(
                        ReconciliationResult.transaction_id == t_id,
                        ReconciliationResult.bank_transaction_id == b_id,
                    )
                )
            elif t_id:
                existing_result = db.scalar(
                    select(ReconciliationResult).where(
                        ReconciliationResult.transaction_id == t_id,
                        ReconciliationResult.bank_transaction_id.is_(None),
                    )
                )
            elif b_id:
                existing_result = db.scalar(
                    select(ReconciliationResult).where(
                        ReconciliationResult.bank_transaction_id == b_id,
                        ReconciliationResult.transaction_id.is_(None),
                    )
                )

            # Build or update result
            result_obj = build_reconciliation_result(cand, existing_result)
            if not existing_result:
                db.add(result_obj)
            db.flush()

            # Handle Exceptions (check existing exception to avoid duplicates across all lifecycle states)
            new_exc = build_exception_for_candidate(cand, reconciliation_id=result_obj.id)
            if new_exc:
                existing_exc = db.scalar(
                    select(PaymentException).where(
                        PaymentException.reconciliation_id == result_obj.id,
                        PaymentException.category == new_exc.category,
                    )
                )
                if not existing_exc:
                    db.add(new_exc)

        db.commit()

        # 5. Compute accuracy
        total_gtxns = len(gateway_txns)
        accuracy = (
            round((counts["matched"] / total_gtxns) * 100, 2)
            if total_gtxns > 0
            else 0.0
        )

        logger.info(
            "Reconciliation run completed for merchant_id=%s: matched=%d, mismatches=%d, "
            "missing_bank=%d, missing_gateway=%d, duplicates=%d, accuracy=%.2f%%",
            merchant_id,
            counts["matched"],
            counts["amount_mismatch"],
            counts["missing_in_bank"],
            counts["missing_in_gateway"],
            counts["duplicate"],
            accuracy,
        )

        return ReconciliationSummaryResponse(
            total_gateway_transactions=total_gtxns,
            total_bank_transactions=len(bank_txns),
            matched=counts["matched"],
            partial_match=counts["partial_match"],
            amount_mismatch=counts["amount_mismatch"],
            missing_in_bank=counts["missing_in_bank"],
            missing_in_gateway=counts["missing_in_gateway"],
            duplicates=counts["duplicate"],
            unresolved=counts["unresolved"],
            delayed=counts["delayed"],
            total_expected_amount=total_expected,
            total_actual_amount=total_actual,
            total_difference=total_difference,
            reconciliation_accuracy=accuracy,
        )

    @staticmethod
    def get_results(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        merchant_id: Optional[uuid.UUID] = None,
        match_status: Optional[MatchStatus] = None,
        min_confidence: Optional[Decimal] = None,
        max_confidence: Optional[Decimal] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Tuple[List[ReconciliationResult], int]:
        """Query reconciliation results with filtering and pagination."""
        stmt = select(ReconciliationResult)
        count_stmt = select(func.count(ReconciliationResult.id))

        if merchant_id:
            stmt = stmt.outerjoin(Transaction, ReconciliationResult.transaction_id == Transaction.id)
            count_stmt = count_stmt.outerjoin(Transaction, ReconciliationResult.transaction_id == Transaction.id)
            stmt = stmt.where(Transaction.merchant_id == merchant_id)
            count_stmt = count_stmt.where(Transaction.merchant_id == merchant_id)

        if match_status:
            stmt = stmt.where(ReconciliationResult.match_status == match_status)
            count_stmt = count_stmt.where(ReconciliationResult.match_status == match_status)

        if min_confidence is not None:
            stmt = stmt.where(ReconciliationResult.confidence_score >= min_confidence)
            count_stmt = count_stmt.where(ReconciliationResult.confidence_score >= min_confidence)

        if max_confidence is not None:
            stmt = stmt.where(ReconciliationResult.confidence_score <= max_confidence)
            count_stmt = count_stmt.where(ReconciliationResult.confidence_score <= max_confidence)

        if date_from:
            stmt = stmt.where(ReconciliationResult.reconciled_at >= date_from)
            count_stmt = count_stmt.where(ReconciliationResult.reconciled_at >= date_from)

        if date_to:
            stmt = stmt.where(ReconciliationResult.reconciled_at <= date_to)
            count_stmt = count_stmt.where(ReconciliationResult.reconciled_at <= date_to)

        total = db.scalar(count_stmt) or 0
        offset = (page - 1) * page_size
        stmt = stmt.order_by(desc(ReconciliationResult.reconciled_at)).offset(offset).limit(page_size)

        items = list(db.scalars(stmt).all())
        return items, total

    @staticmethod
    def get_result_by_id(
        result_id: uuid.UUID,
        db: Session,
    ) -> Optional[ReconciliationResult]:
        """Fetch single reconciliation result with related exceptions."""
        stmt = (
            select(ReconciliationResult)
            .options(selectinload(ReconciliationResult.exceptions))
            .where(ReconciliationResult.id == result_id)
        )
        return db.scalar(stmt)

    @staticmethod
    def get_summary(
        merchant_id: Optional[uuid.UUID],
        db: Session,
    ) -> ReconciliationSummaryResponse:
        """Compute summary metrics from current database state."""
        gtxn_count = db.scalar(
            select(func.count(Transaction.id)).where(
                Transaction.merchant_id == merchant_id if merchant_id else True
            )
        ) or 0

        btxn_count = db.scalar(select(func.count(BankTransaction.id))) or 0

        # Query result statistics
        base_query = select(ReconciliationResult)
        if merchant_id:
            base_query = base_query.outerjoin(
                Transaction, ReconciliationResult.transaction_id == Transaction.id
            ).where(Transaction.merchant_id == merchant_id)

        results = list(db.scalars(base_query).all())

        counts = {
            "matched": 0,
            "partial_match": 0,
            "amount_mismatch": 0,
            "missing_in_bank": 0,
            "missing_in_gateway": 0,
            "duplicate": 0,
            "unresolved": 0,
            "delayed": 0,
        }

        total_exp = Decimal("0.0000")
        total_act = Decimal("0.0000")
        total_diff = Decimal("0.0000")

        for r in results:
            st = r.match_status.value
            if st in counts:
                counts[st] += 1
            if r.matching_method and "delayed" in r.matching_method:
                counts["delayed"] += 1

            if r.expected_amount is not None:
                total_exp += r.expected_amount
            if r.actual_amount is not None:
                total_act += r.actual_amount
            if r.difference_amount is not None:
                total_diff += r.difference_amount

        acc = (
            round((counts["matched"] / gtxn_count) * 100, 2)
            if gtxn_count > 0
            else 0.0
        )

        return ReconciliationSummaryResponse(
            total_gateway_transactions=gtxn_count,
            total_bank_transactions=btxn_count,
            matched=counts["matched"],
            partial_match=counts["partial_match"],
            amount_mismatch=counts["amount_mismatch"],
            missing_in_bank=counts["missing_in_bank"],
            missing_in_gateway=counts["missing_in_gateway"],
            duplicates=counts["duplicate"],
            unresolved=counts["unresolved"],
            delayed=counts["delayed"],
            total_expected_amount=total_exp,
            total_actual_amount=total_act,
            total_difference=total_diff,
            reconciliation_accuracy=acc,
        )
