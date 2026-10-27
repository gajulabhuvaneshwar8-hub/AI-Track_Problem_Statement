"""
app/services/ai/__init__.py

Package initialization for AI reconciliation analysis services.
"""

from app.services.ai.ai_client import AIClient, AIAvailabilityError, default_ai_client
from app.services.ai.ai_service import (
    analyze_exception,
    analyze_reconciliation_result,
    get_analyses_for_reconciliation,
    get_analysis,
    investigate_exception,
    list_analyses,
)
from app.services.ai.exception_analyzer import build_safe_context, run_analysis
from app.services.ai.fallback_analyzer import analyze_fallback
from app.services.ai.recommendation_service import generate_recommendations
from app.services.ai.response_parser import (
    AIResponseParseError,
    clean_llm_json_text,
    parse_ai_response,
)
from app.services.ai.root_cause_analyzer import analyze_root_cause

__all__ = [
    "AIClient",
    "AIAvailabilityError",
    "default_ai_client",
    "run_analysis",
    "build_safe_context",
    "analyze_fallback",
    "clean_llm_json_text",
    "parse_ai_response",
    "AIResponseParseError",
    "analyze_root_cause",
    "generate_recommendations",
    "analyze_reconciliation_result",
    "analyze_exception",
    "investigate_exception",
    "list_analyses",
    "get_analysis",
    "get_analyses_for_reconciliation",
]
