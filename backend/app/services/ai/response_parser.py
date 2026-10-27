"""
app/services/ai/response_parser.py

Sanitizes, parses, and validates responses returned by LLM providers.
Treats AI output as untrusted input.
Ensures all required fields are present, properly typed, and strictly bounded.
"""

from __future__ import annotations

import json
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Dict

from app.models.enums import RiskLevel

logger = logging.getLogger(__name__)


class AIResponseParseError(ValueError):
    """Raised when an AI response cannot be parsed or validated."""
    pass


def clean_llm_json_text(raw_text: str) -> str:
    """
    Strips Markdown code fences and surrounding whitespace from raw LLM output.
    Handles ```json ... ```, ``` ... ```, and inline whitespace.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()
    # Match ```json ... ``` or ``` ... ```
    fence_pattern = r"^```(?:json)?\s*(.*?)\s*```$"
    match = re.search(fence_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1).strip()
    elif text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE)
        text = re.sub(r"```$", "", text).strip()

    return text


def parse_ai_response(raw_text: str) -> Dict[str, Any]:
    """
    Parses and validates structured JSON response from an LLM.

    Returns normalized dict:
      - summary (str)
      - root_cause (str)
      - impact (str)
      - recommended_action (str)
      - risk_level (RiskLevel)
      - confidence_score (Decimal)

    Raises AIResponseParseError on invalid JSON or missing mandatory content.
    """
    cleaned_text = clean_llm_json_text(raw_text)
    if not cleaned_text:
        raise AIResponseParseError("Empty response received from AI provider.")

    try:
        data = json.loads(cleaned_text)
    except json.JSONDecodeError as exc:
        logger.warning("AI response is not valid JSON: %s (Raw: %s)", exc, raw_text[:200])
        raise AIResponseParseError(f"Malformed JSON from AI provider: {exc}") from exc

    if not isinstance(data, dict):
        raise AIResponseParseError("AI response must be a JSON object dictionary.")

    summary = str(data.get("summary") or "").strip()
    if not summary:
        raise AIResponseParseError("AI response missing mandatory 'summary' field.")

    root_cause = str(data.get("root_cause") or "").strip() or None
    impact = str(data.get("impact") or "").strip() or None
    recommended_action = str(data.get("recommended_action") or "").strip() or None

    # Validate risk level
    raw_risk = str(data.get("risk_level") or "medium").lower().strip()
    if raw_risk in {r.value for r in RiskLevel}:
        risk_level = RiskLevel(raw_risk)
    else:
        logger.info("Unrecognized risk_level %r; defaulting to medium", raw_risk)
        risk_level = RiskLevel.medium

    # Validate confidence score
    raw_conf = data.get("confidence_score")
    try:
        if raw_conf is not None:
            conf_dec = Decimal(str(raw_conf))
            if conf_dec < 0:
                conf_dec = Decimal("0.0000")
            elif conf_dec > 1:
                conf_dec = Decimal("1.0000")
            confidence_score = conf_dec.quantize(Decimal("0.0001"))
        else:
            confidence_score = Decimal("0.8500")
    except (InvalidOperation, TypeError, ValueError):
        confidence_score = Decimal("0.8500")

    return {
        "summary": summary,
        "root_cause": root_cause,
        "impact": impact,
        "recommended_action": recommended_action,
        "risk_level": risk_level,
        "confidence_score": confidence_score,
    }
