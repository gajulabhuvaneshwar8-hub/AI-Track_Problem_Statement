"""
app/services/reconciliation/duplicate_detector.py

Duplicate detection for gateway transactions and bank statements.
Uses normalized references, amounts, and dates to identify duplicate records.
"""

import re
from typing import Dict, List, Set, Tuple
from app.models.transaction import Transaction
from app.models.bank_transaction import BankTransaction


def normalize_reference(ref: str) -> str:
    """
    Normalize transaction references for fuzzy matching and deduplication.
    Converts to uppercase and removes spaces, dashes, underscores, and special chars.
    Example: 'TXN-001' -> 'TXN001', 'txn_001' -> 'TXN001'.
    """
    if not ref:
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(ref).strip().upper())


def find_gateway_duplicates(
    transactions: List[Transaction],
) -> Tuple[List[Transaction], Set[str]]:
    """
    Identify duplicate gateway transactions based on normalized reference
    and exact suspicious fingerprints (same normalized ref + amount + date).
    Returns: (duplicate_transactions, duplicate_norm_refs)
    """
    seen_norm_refs: Dict[str, Transaction] = {}
    duplicates: List[Transaction] = []
    duplicate_refs: Set[str] = set()

    for txn in transactions:
        norm_ref = normalize_reference(txn.transaction_reference)
        if not norm_ref:
            continue

        if norm_ref in seen_norm_refs:
            duplicates.append(txn)
            duplicate_refs.add(norm_ref)
        else:
            seen_norm_refs[norm_ref] = txn

    return duplicates, duplicate_refs


def find_bank_duplicates(
    bank_transactions: List[BankTransaction],
) -> Tuple[List[BankTransaction], Set[str]]:
    """
    Identify duplicate bank statement transactions based on normalized bank_reference.
    Returns: (duplicate_bank_txns, duplicate_bank_refs)
    """
    seen_refs: Dict[str, BankTransaction] = {}
    duplicates: List[BankTransaction] = []
    duplicate_refs: Set[str] = set()

    for btxn in bank_transactions:
        norm_ref = normalize_reference(btxn.bank_reference)
        if not norm_ref:
            continue

        if norm_ref in seen_refs:
            duplicates.append(btxn)
            duplicate_refs.add(norm_ref)
        else:
            seen_refs[norm_ref] = btxn

    return duplicates, duplicate_refs
