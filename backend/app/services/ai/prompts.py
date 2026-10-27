"""
app/services/ai/prompts.py

Centralized AI prompts for financial reconciliation exception analysis.
Enforces strict domain boundaries:
  - Authoritative reconciliation status (cannot be overridden)
  - No synthetic financial data or hallucinated causes
  - Clear separation between possible causes vs confirmed causes
  - Strict JSON response contract
"""

from __future__ import annotations

import json
from typing import Any, Dict

SYSTEM_PROMPT = """You are a financial reconciliation analysis assistant.

The reconciliation result provided to you is authoritative.
Do not change or reinterpret the reconciliation status.
Analyze the provided evidence only.
If evidence is insufficient, explicitly say that more investigation is required.
Never invent transaction details, amounts, dates, bank records, or causes.

You must clearly distinguish between a "possible cause" and a "confirmed cause".
Never state an unverified explanation as fact.

Return your response ONLY as a valid JSON object with the following structure:
{
  "summary": "<Concise human-readable explanation of the mismatch or exception>",
  "root_cause": "<Identified or suspected root causes, clearly marked as potential/confirmed>",
  "impact": "<Financial, operational, or customer risk impact of this discrepancy>",
  "recommended_action": "<Concrete, step-by-step next action for finance controllers>",
  "risk_level": "low|medium|high|critical",
  "confidence_score": 0.00
}
Do not include any Markdown text outside the JSON object.
"""

ANALYSIS_INSTRUCTIONS = {
    "amount_mismatch": """
SPECIAL INSTRUCTION FOR AMOUNT MISMATCH:
- Detail the expected amount, actual amount, and absolute difference.
- Analyze potential factors: bank transaction fees, merchant discount rate (MDR) deductions, currency conversion, partial capture, refund deduction, or settlement adjustment.
- Explicitly state: "Possible cause (not confirmed): ..."
- Assess financial impact based on the magnitude and percentage of the difference.
""",
    "missing_in_bank": """
SPECIAL INSTRUCTION FOR MISSING IN BANK:
- The transaction exists in the payment gateway but has no corresponding bank deposit/settlement record.
- Consider delayed settlement cycles (T+1 / T+2), bank processing holidays, failed settlement payout, or gateway batching lag.
- Recommend: Verify payment gateway payout batch, check bank statement around the expected settlement window, verify merchant settlement account.
""",
    "missing_in_gateway": """
SPECIAL INSTRUCTION FOR MISSING IN GATEWAY:
- A bank deposit/credit was received without an originating gateway transaction record.
- Consider manual bank transfers, direct customer NEFT/RTGS, missing gateway export data, chargeback reversal credit, or unmapped merchant identifier.
- Recommend: Verify gateway export completeness, inspect customer reference in bank narration, confirm if manual bank transfer occurred.
""",
    "duplicate": """
SPECIAL INSTRUCTION FOR DUPLICATE TRANSACTION:
- Multiple records share identical references or identical amount/timestamp footprints.
- Highlight risk of double-crediting or duplicate customer charging.
- Recommend: Verify if duplicate API callback occurred, check raw CSV/Excel file uploads for duplicate rows, inspect bank narration.
""",
    "delayed": """
SPECIAL INSTRUCTION FOR DELAYED SETTLEMENT:
- Highlight the date variance between gateway transaction authorization and bank statement credit.
- Evaluate whether this delay breaches SLA or standard settlement windows.
- Recommend: Check gateway settlement schedule, check bank clearing holidays, verify liquidity impact.
""",
    "status_mismatch": """
SPECIAL INSTRUCTION FOR STATUS MISMATCH:
- Gateway status contradicts Bank status (e.g. Gateway SUCCESS vs Bank FAILED / REVERSED).
- THIS IS A HIGH/CRITICAL RISK SCENARIO.
- Highlight immediate risk: merchant order may have been fulfilled for a failed payment, or customer may have been debited without credit.
- Recommend IMMEDIATE human escalation and suspension of related merchant disbursements until confirmed. Never auto-resolve.
""",
    "unresolved": """
SPECIAL INSTRUCTION FOR UNRESOLVED DISCREPANCY:
- Ambiguous match with multiple potential candidates or low confidence.
- Detail the candidate options and why an automated decision cannot be safely made.
- Recommend: Manual human review and controller sign-off.
""",
}


def build_analysis_prompt(
    context: Dict[str, Any],
    analysis_type: str = "exception_analysis",
) -> str:
    """
    Constructs a controlled, prompt string with sanitized transaction/reconciliation context.
    """
    match_status = context.get("reconciliation", {}).get("match_status", "")
    specific_instruction = ANALYSIS_INSTRUCTIONS.get(match_status, "")

    context_json = json.dumps(context, indent=2, default=str)

    prompt = f"""Task: Conduct a rigorous financial reconciliation {analysis_type.replace('_', ' ')}.

Context:
{context_json}

{specific_instruction}

Analyze this discrepancy and return the structured JSON response as specified in the system prompt.
"""
    return prompt.strip()
