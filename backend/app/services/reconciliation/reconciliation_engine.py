"""
app/services/reconciliation/reconciliation_engine.py

Pure computational reconciliation engine.
Compares gateway transactions and bank statements through a deterministic matching hierarchy:
1. Duplicate detection
2. Level 1: Exact reference match
3. Level 2: Normalized reference match
4. Level 3: Amount + Date fallback match
5. Missing in bank / Missing in gateway classification
"""

from decimal import Decimal
from typing import Dict, List, Optional, Set

from app.models.bank_transaction import BankTransaction
from app.models.enums import MatchStatus
from app.models.transaction import Transaction
from app.services.reconciliation.date_matcher import (
    DEFAULT_DATE_TOLERANCE_DAYS,
    DEFAULT_DELAY_THRESHOLD_DAYS,
    DEFAULT_SEVERE_DELAY_THRESHOLD_DAYS,
    is_within_date_tolerance,
)
from app.services.reconciliation.duplicate_detector import (
    find_bank_duplicates,
    find_gateway_duplicates,
    normalize_reference,
)
from app.services.reconciliation.matching_engine import MatchCandidate, evaluate_pair


class ReconciliationEngine:
    """Orchestrates deterministic transaction matching between gateway and bank records."""

    def __init__(
        self,
        date_tolerance_days: int = DEFAULT_DATE_TOLERANCE_DAYS,
        delay_threshold_days: int = DEFAULT_DELAY_THRESHOLD_DAYS,
        severe_delay_threshold_days: int = DEFAULT_SEVERE_DELAY_THRESHOLD_DAYS,
    ):
        self.date_tolerance_days = date_tolerance_days
        self.delay_threshold_days = delay_threshold_days
        self.severe_delay_threshold_days = severe_delay_threshold_days

    def reconcile(
        self,
        gateway_transactions: List[Transaction],
        bank_transactions: List[BankTransaction],
    ) -> List[MatchCandidate]:
        """Execute the full matching hierarchy and produce MatchCandidate records."""
        results: List[MatchCandidate] = []

        # ------------------------------------------------------------------
        # 1. Duplicate Detection
        # ------------------------------------------------------------------
        gtxn_dups, gtxn_dup_refs = find_gateway_duplicates(gateway_transactions)
        btxn_dups, btxn_dup_refs = find_bank_duplicates(bank_transactions)

        dup_gtxn_ids = {t.id for t in gtxn_dups}
        dup_btxn_ids = {b.id for b in btxn_dups}

        for t in gtxn_dups:
            results.append(
                MatchCandidate(
                    transaction=t,
                    bank_transaction=None,
                    match_status=MatchStatus.duplicate,
                    confidence_score=Decimal("0.0000"),
                    matching_method="duplicate",
                    expected_amount=t.amount,
                    actual_amount=None,
                    difference_amount=None,
                    explanation=f"Duplicate gateway transaction with reference '{t.transaction_reference}'.",
                )
            )

        for b in btxn_dups:
            results.append(
                MatchCandidate(
                    transaction=None,
                    bank_transaction=b,
                    match_status=MatchStatus.duplicate,
                    confidence_score=Decimal("0.0000"),
                    matching_method="duplicate",
                    expected_amount=None,
                    actual_amount=b.amount,
                    difference_amount=None,
                    explanation=f"Duplicate bank transaction with reference '{b.bank_reference}'.",
                )
            )

        # Candidates eligible for matching
        active_gtxns = [t for t in gateway_transactions if t.id not in dup_gtxn_ids]
        active_btxns = [b for b in bank_transactions if b.id not in dup_btxn_ids]

        matched_gtxn_ids: Set = set()
        matched_btxn_ids: Set = set()

        # Build bank lookups
        # Direct references:
        bank_by_txn_ref: Dict[str, BankTransaction] = {}
        bank_by_bank_ref: Dict[str, BankTransaction] = {}
        # Normalized references:
        norm_bank_by_txn_ref: Dict[str, BankTransaction] = {}
        norm_bank_by_bank_ref: Dict[str, BankTransaction] = {}

        for b in active_btxns:
            if b.transaction_reference:
                raw = b.transaction_reference.strip()
                bank_by_txn_ref[raw] = b
                norm_bank_by_txn_ref[normalize_reference(raw)] = b

            raw_bref = b.bank_reference.strip()
            bank_by_bank_ref[raw_bref] = b
            norm_bank_by_bank_ref[normalize_reference(raw_bref)] = b

        # ------------------------------------------------------------------
        # 2. Level 1 — Exact Reference Match
        # ------------------------------------------------------------------
        for gtxn in active_gtxns:
            raw_ref = gtxn.transaction_reference.strip()
            target_btxn = bank_by_txn_ref.get(raw_ref) or bank_by_bank_ref.get(raw_ref)

            if target_btxn and target_btxn.id not in matched_btxn_ids:
                candidate = evaluate_pair(gtxn, target_btxn, method_prefix="exact_reference")
                results.append(candidate)
                matched_gtxn_ids.add(gtxn.id)
                matched_btxn_ids.add(target_btxn.id)

        # ------------------------------------------------------------------
        # 3. Level 2 — Normalized Reference Match
        # ------------------------------------------------------------------
        for gtxn in active_gtxns:
            if gtxn.id in matched_gtxn_ids:
                continue

            norm_ref = normalize_reference(gtxn.transaction_reference)
            target_btxn = norm_bank_by_txn_ref.get(norm_ref) or norm_bank_by_bank_ref.get(norm_ref)

            if target_btxn and target_btxn.id not in matched_btxn_ids:
                candidate = evaluate_pair(gtxn, target_btxn, method_prefix="normalized_reference")
                results.append(candidate)
                matched_gtxn_ids.add(gtxn.id)
                matched_btxn_ids.add(target_btxn.id)

        # ------------------------------------------------------------------
        # 4. Level 3 — Amount + Date Fallback Match
        # ------------------------------------------------------------------
        unmatched_btxns = [b for b in active_btxns if b.id not in matched_btxn_ids]

        for gtxn in active_gtxns:
            if gtxn.id in matched_gtxn_ids:
                continue

            candidates = [
                b for b in unmatched_btxns
                if b.id not in matched_btxn_ids
                and b.amount == gtxn.amount
                and is_within_date_tolerance(
                    gtxn.transaction_date, b.transaction_date, self.date_tolerance_days
                )
            ]

            if len(candidates) == 1:
                # Unique single candidate match
                btxn = candidates[0]
                results.append(
                    MatchCandidate(
                        transaction=gtxn,
                        bank_transaction=btxn,
                        match_status=MatchStatus.matched,
                        confidence_score=Decimal("0.8000"),
                        matching_method="amount_date_fallback",
                        expected_amount=gtxn.amount,
                        actual_amount=btxn.amount,
                        difference_amount=Decimal("0.0000"),
                        explanation=(
                            f"Matched via amount ({gtxn.amount} {gtxn.currency or 'USD'}) "
                            f"and date window fallback."
                        ),
                    )
                )
                matched_gtxn_ids.add(gtxn.id)
                matched_btxn_ids.add(btxn.id)
            elif len(candidates) > 1:
                # Multiple candidates — marked unresolved, no arbitrary choice!
                results.append(
                    MatchCandidate(
                        transaction=gtxn,
                        bank_transaction=None,
                        match_status=MatchStatus.unresolved,
                        confidence_score=Decimal("0.3000"),
                        matching_method="amount_date_fallback",
                        expected_amount=gtxn.amount,
                        actual_amount=None,
                        difference_amount=None,
                        explanation=(
                            f"Multiple ({len(candidates)}) candidate bank transactions found "
                            f"for the same amount ({gtxn.amount}) and date range."
                        ),
                        has_multiple_candidates=True,
                    )
                )
                matched_gtxn_ids.add(gtxn.id)

        # ------------------------------------------------------------------
        # 5. Missing in Bank (remaining unmatched gateway transactions)
        # ------------------------------------------------------------------
        for gtxn in active_gtxns:
            if gtxn.id not in matched_gtxn_ids:
                results.append(
                    MatchCandidate(
                        transaction=gtxn,
                        bank_transaction=None,
                        match_status=MatchStatus.missing_in_bank,
                        confidence_score=Decimal("0.0000"),
                        matching_method="no_bank_match",
                        expected_amount=gtxn.amount,
                        actual_amount=Decimal("0.0000"),
                        difference_amount=-gtxn.amount,
                        explanation=(
                            f"Gateway transaction '{gtxn.transaction_reference}' "
                            f"has no corresponding bank record."
                        ),
                    )
                )
                matched_gtxn_ids.add(gtxn.id)

        # ------------------------------------------------------------------
        # 6. Missing in Gateway (remaining unmatched bank transactions)
        # ------------------------------------------------------------------
        for btxn in active_btxns:
            if btxn.id not in matched_btxn_ids:
                results.append(
                    MatchCandidate(
                        transaction=None,
                        bank_transaction=btxn,
                        match_status=MatchStatus.missing_in_gateway,
                        confidence_score=Decimal("0.0000"),
                        matching_method="no_gateway_match",
                        expected_amount=Decimal("0.0000"),
                        actual_amount=btxn.amount,
                        difference_amount=btxn.amount,
                        explanation=(
                            f"Bank transaction '{btxn.bank_reference}' "
                            f"has no corresponding gateway record."
                        ),
                    )
                )
                matched_btxn_ids.add(btxn.id)

        return results
