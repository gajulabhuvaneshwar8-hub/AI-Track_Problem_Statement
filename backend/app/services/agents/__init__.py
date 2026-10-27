"""
app/services/agents/__init__.py

AI Reconciliation Investigation Agent package.
Exports the core agent components:
  - ReconciliationAgent
  - InvestigationContext
  - EvidenceCollector
  - DecisionEngine
  - EscalationService
  - agent_tools
  - agent_logger
  - investigation_service
"""

from app.services.agents.agent_logger import log_investigation_event
from app.services.agents.decision_engine import DecisionEngine, DecisionOutcome
from app.services.agents.escalation_service import EscalationRecommendation, EscalationService
from app.services.agents.evidence_collector import EvidenceCollector
from app.services.agents.investigation_context import InvestigationContext
from app.services.agents.reconciliation_agent import ReconciliationAgent

__all__ = [
    "ReconciliationAgent",
    "InvestigationContext",
    "EvidenceCollector",
    "DecisionEngine",
    "DecisionOutcome",
    "EscalationService",
    "EscalationRecommendation",
    "log_investigation_event",
]
