"""
app/services/ai/fallback_analyzer.py

Deterministic rule-based fallback analyzer.
Used whenever the external AI provider is unavailable, unconfigured (missing AI_API_KEY),
times out, or returns an invalid payload.

Produces consistent, auditable, domain-accurate explanations without network calls.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

from app.models.enums import AnalysisStatus, RiskLevel


def analyze_fallback(
    context: Dict[str, Any],
    analysis_type: str = "exception_analysis",
) -> Dict[str, Any]:
    """
    Generates a deterministic fallback analysis based on structured reconciliation evidence.
    Always returns valid fields with status="fallback" and ai_provider="fallback".
    """
    recon = context.get("reconciliation") or {}
    exc = context.get("exception") or {}
    txn = context.get("transaction") or {}
    bank_txn = context.get("bank_transaction") or {}

    match_status = str(recon.get("match_status") or "").lower()
    diff_amount = recon.get("difference_amount")
    currency = txn.get("currency") or "INR"
    txn_status = str(txn.get("status") or "").lower()
    bank_status = str(bank_txn.get("status") or "").lower()

    # Default fallback values
    risk_level = RiskLevel.medium
    confidence_score = Decimal("0.8500")

    # -----------------------------------------------------------------------
    # Case 1: Amount mismatch
    # -----------------------------------------------------------------------
    if match_status == "amount_mismatch":
        expected = recon.get("expected_amount")
        actual = recon.get("actual_amount")
        diff_str = f"{currency} {abs(Decimal(str(diff_amount))):.2f}" if diff_amount is not None else "variance"
        summary = (
            f"Payment amount mismatch detected. Expected {currency} {expected}, but bank record indicates "
            f"{currency} {actual} (discrepancy of {diff_str})."
        )
        root_cause = (
            "Possible causes (unconfirmed): Bank processing fee or MDR deduction, partial authorization capture, "
            "subsequent partial refund, or settlement currency conversion variance."
        )
        impact = (
            f"Financial variance of {diff_str}. If left unreconciled, ledger balances between payment gateway "
            f"and bank depository will not balance."
        )
        recommended_action = (
            "Compare the gateway settlement report fee breakdown against bank deposit credit line items. "
            "Verify whether any MDR or chargeback deduction was applied."
        )
        risk_level = RiskLevel.high if (diff_amount and abs(Decimal(str(diff_amount))) > 500) else RiskLevel.medium
        confidence_score = Decimal("0.9000")

    # -----------------------------------------------------------------------
    # Case 2: Missing in bank
    # -----------------------------------------------------------------------
    elif match_status == "missing_in_bank":
        txn_ref = txn.get("transaction_reference") or "Gateway transaction"
        summary = (
            f"Gateway transaction '{txn_ref}' was recorded successfully, but no corresponding bank "
            f"deposit or settlement record was identified."
        )
        root_cause = (
            "Possible causes (unconfirmed): Payout settlement cycle delay (T+1/T+2), bank processing cutoff or "
            "holiday lag, failed payout disbursement from the gateway, or mismatched bank account."
        )
        impact = (
            "Potential unrealized revenue or funds held in gateway settlement account without bank credit. "
            "Cash flow tracking is delayed."
        )
        recommended_action = (
            "Check gateway payout batch status for the transaction date. Verify whether the payout batch has cleared "
            "and request a settlement UTR from the gateway partner."
        )
        risk_level = RiskLevel.high
        confidence_score = Decimal("0.9200")

    # -----------------------------------------------------------------------
    # Case 3: Missing in gateway
    # -----------------------------------------------------------------------
    elif match_status == "missing_in_gateway":
        bank_ref = bank_txn.get("bank_reference") or "Bank entry"
        amount = bank_txn.get("amount")
        summary = (
            f"Bank deposit entry '{bank_ref}' of {currency} {amount} exists on the bank statement, "
            f"but no originating gateway payment record was located."
        )
        root_cause = (
            "Possible causes (unconfirmed): Direct customer wire transfer (NEFT/RTGS/IMPS) bypassing payment gateway, "
            "delayed or dropped gateway webhook/export data, or unmapped payment source."
        )
        impact = (
            "Unallocated cash balance in bank account. Risk of unidentified revenue or customer account misallocation."
        )
        recommended_action = (
            "Review bank statement narration for customer identifiers, check gateway export logs for missing records, "
            "and verify with operations if an offline payment was processed."
        )
        risk_level = RiskLevel.high
        confidence_score = Decimal("0.8800")

    # -----------------------------------------------------------------------
    # Case 4: Duplicate transaction
    # -----------------------------------------------------------------------
    elif match_status == "duplicate":
        ref = txn.get("transaction_reference") or bank_txn.get("transaction_reference") or "Reference"
        summary = (
            f"Duplicate record detected for transaction reference '{ref}'. "
            f"Multiple matching records exist in the ingested data."
        )
        root_cause = (
            "Possible causes (unconfirmed): Repeated file upload, redundant API webhook callback, "
            "or accidental double billing of the customer."
        )
        impact = (
            "Risk of duplicate customer debit, inaccurate revenue inflation, or operational reconciliation double-counting."
        )
        recommended_action = (
            "Inspect raw upload batch files for repeated lines. Verify whether customer was charged multiple times "
            "or if a duplicate import occurred. Do not issue payout until verified."
        )
        risk_level = RiskLevel.high
        confidence_score = Decimal("0.9500")

    # -----------------------------------------------------------------------
    # Case 5: Delayed settlement
    # -----------------------------------------------------------------------
    elif match_status == "delayed" or (exc.get("category") == "timing_delay"):
        txn_date = txn.get("transaction_date")
        bank_date = bank_txn.get("transaction_date")
        summary = (
            f"Settlement timing delay observed between gateway transaction date ({txn_date}) "
            f"and bank credit date ({bank_date})."
        )
        root_cause = (
            "Possible causes (unconfirmed): Gateway batch processing schedule, weekend or bank clearing holiday, "
            "or extended liquidity holding window by processor."
        )
        impact = (
            "Working capital delay and minor SLA breach. Funds are safe once confirmed in bank."
        )
        recommended_action = (
            "Verify processor contractual settlement SLAs. No ledger correction needed if amounts match and "
            "delay is within acceptable business parameters."
        )
        risk_level = RiskLevel.low
        confidence_score = Decimal("0.9000")

    # -----------------------------------------------------------------------
    # Case 6: Status mismatch (Gateway SUCCESS vs Bank FAILED)
    # -----------------------------------------------------------------------
    elif (
        (txn_status in {"success", "completed"} and bank_status in {"failed", "reversed"})
        or (txn_status in {"failed", "reversed"} and bank_status in {"posted", "success"})
        or ("status" in str(exc.get("category") or "").lower())
    ):
        summary = (
            f"Critical status conflict detected: Gateway status is '{txn_status.upper()}' whereas Bank status "
            f"is '{bank_status.upper()}'."
        )
        root_cause = (
            "Possible causes (unconfirmed): Post-authorization reversal, chargeback dispute, technical drop after "
            "gateway authorization, or settlement rejection."
        )
        impact = (
            "CRITICAL EXPOSURE: Goods/services may have been delivered for a failed payment, or customer funds "
            "were captured despite bank rejection."
        )
        recommended_action = (
            "IMMEDIATE HUMAN INVESTIGATION REQUIRED. Suspend merchant order fulfillment or payout disbursement. "
            "Confirm definitive bank status with depository branch before resolving."
        )
        risk_level = RiskLevel.critical
        confidence_score = Decimal("0.9600")

    # -----------------------------------------------------------------------
    # Case 7: Unresolved / Ambiguous
    # -----------------------------------------------------------------------
    else:
        summary = (
            "Transaction reconciliation could not be conclusively determined. Multiple candidates or "
            "insufficient matching confidence exists."
        )
        root_cause = (
            "Ambiguous matching criteria; potential multiple payments with identical amounts or missing references."
        )
        impact = (
            "Indeterminate financial status requiring manual review to prevent misattribution."
        )
        recommended_action = (
            "Review transaction notes and bank narration manually. Do not automate resolution."
        )
        risk_level = RiskLevel.medium
        confidence_score = Decimal("0.7500")

    # Tailor if analysis_type is specific
    if analysis_type == "root_cause":
        summary = f"Root Cause Analysis: {summary}"
    elif analysis_type == "recommendation":
        summary = f"Action Recommendation: {recommended_action}"

    return {
        "summary": summary,
        "root_cause": root_cause,
        "impact": impact,
        "recommended_action": recommended_action,
        "risk_level": risk_level,
        "confidence_score": confidence_score,
        "status": AnalysisStatus.fallback,
        "ai_provider": "fallback",
        "model_name": "rule-based-fallback-v1",
        "raw_response": "Generated by rule-based fallback analyzer (external AI unavailable or bypassed).",
    }
