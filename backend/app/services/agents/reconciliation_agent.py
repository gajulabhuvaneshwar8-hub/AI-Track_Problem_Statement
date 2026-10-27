"""
app/services/agents/reconciliation_agent.py

ReconciliationAgent orchestrator for Step 7.
Coordinates automated exception investigation, empirical evidence collection,
deterministic decision execution, AI/fallback natural language synthesis,
auditing, and escalation packaging.

FINANCIAL IMMUTABILITY BOUNDARY:
- Strictly read-only for financial ledgers, transactions, and settlements.
- Deterministic decision rules control final MONITOR / REVIEW / ESCALATE outcomes.
- AI provides root cause hypotheses, explanations, and recommendation text.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.agent_investigation import AgentInvestigation
from app.models.enums import AgentDecision, InvestigationStatus, RiskLevel
from app.models.exception import PaymentException
from app.models.reconciliation_result import ReconciliationResult
from app.models.user import User
from app.services import audit_service
from app.services.agents import agent_tools
from app.services.agents.agent_logger import log_investigation_event
from app.services.agents.decision_engine import DecisionEngine, DecisionOutcome
from app.services.agents.escalation_service import EscalationRecommendation, EscalationService
from app.services.agents.evidence_collector import EvidenceCollector
from app.services.agents.investigation_context import InvestigationContext
from app.services.ai.ai_client import AIClient, AIAvailabilityError, default_ai_client
from app.services.ai.fallback_analyzer import analyze_fallback
from app.services.ai.prompts import build_analysis_prompt
from app.services.ai.response_parser import AIResponseParseError, parse_ai_response

logger = logging.getLogger("app.agent.reconciliation_agent")


class ReconciliationAgent:
    """
    AI Reconciliation Investigation Agent orchestrator.
    Behaves like an autonomous finance operations investigation assistant.
    """

    def __init__(
        self,
        db: Session,
        ai_client: Optional[AIClient] = None,
        evidence_collector: Optional[EvidenceCollector] = None,
        decision_engine: Optional[DecisionEngine] = None,
        escalation_service: Optional[EscalationService] = None,
    ):
        self.db = db
        self.ai_client = ai_client or default_ai_client
        self.evidence_collector = evidence_collector or EvidenceCollector(db)
        self.decision_engine = decision_engine or DecisionEngine()
        self.escalation_service = escalation_service or EscalationService()

    def collect_evidence(
        self,
        exception_id: Optional[uuid.UUID] = None,
        reconciliation_id: Optional[uuid.UUID] = None,
    ) -> InvestigationContext:
        """
        Gathers all transaction, bank, reconciliation, settlement, and historical evidence.
        """
        return self.evidence_collector.collect(
            exception_id=exception_id,
            reconciliation_id=reconciliation_id,
        )

    def make_decision(self, context: InvestigationContext) -> DecisionOutcome:
        """
        Runs deterministic business logic to categorize the investigation into MONITOR, REVIEW, or ESCALATE.
        """
        return self.decision_engine.evaluate(context)

    async def analyze_evidence(
        self,
        context: InvestigationContext,
    ) -> Dict[str, Any]:
        """
        Synthesizes natural language explanations, confirmed facts, possible causes,
        and root cause hypotheses via LLM or deterministic fallback.
        """
        recon = context.reconciliation_result
        exc = context.exception
        txn = context.transaction
        btxn = context.bank_transaction
        settlement = context.settlement

        # Generate grounded confirmed facts
        confirmed_facts: List[str] = []
        if txn and txn.amount is not None:
            confirmed_facts.append(f"Gateway authorized amount was ₹{txn.amount} ({txn.currency}) with status '{txn.status.value}'.")
        if btxn and btxn.amount is not None:
            confirmed_facts.append(f"Bank statement reported amount was ₹{btxn.amount} with status '{btxn.status if isinstance(btxn.status, str) else btxn.status.value}'.")
        if recon and recon.difference_amount:
            confirmed_facts.append(f"Variance between ledgers is ₹{recon.difference_amount}.")
        if settlement:
            confirmed_facts.append(f"Settlement batch {settlement.settlement_reference} recorded net ₹{settlement.net_amount} with fees ₹{settlement.fees}.")
        elif not settlement and (txn or btxn):
            confirmed_facts.append("No settlement batch was found matching this transaction date.")

        if not confirmed_facts:
            confirmed_facts.append("Reconciliation evidence collected from available records.")

        # Try AI service synthesis
        safe_context = context.to_safe_dict()
        ai_used = False
        summary = ""
        possible_causes: List[str] = []
        root_cause: Optional[str] = None
        recommended_action: Optional[str] = None

        try:
            prompt = build_analysis_prompt(
                context=safe_context,
                analysis_type="investigation",
            )
            raw_text = await self.ai_client.generate_analysis(prompt)
            parsed = parse_ai_response(raw_text)


            summary = parsed.get("summary") or "AI completed investigation analysis."
            root_cause = parsed.get("root_cause")
            recommended_action = parsed.get("recommended_action")

            # Extract possible causes if returned or derive
            if "discrepancy_factors" in parsed and isinstance(parsed["discrepancy_factors"], list):
                possible_causes = [str(f) for f in parsed["discrepancy_factors"]]
            elif root_cause:
                possible_causes = [root_cause]

            ai_used = True
        except (AIAvailabilityError, AIResponseParseError, Exception) as err:
            logger.warning("AI synthesis unavailable (%s), using rule-based fallback.", str(err))
            fallback = analyze_fallback(
                context=safe_context,
                analysis_type="investigation",
            )
            summary = fallback.get("summary", "Rule-based investigation analysis completed.")
            root_cause = fallback.get("root_cause")
            recommended_action = fallback.get("recommended_action")
            possible_causes = [
                "Bank-side fee deduction",
                "Partial settlement batch",
                "Processing clearing window timing difference",
            ] if recon and recon.match_status.value == "amount_mismatch" else [
                "Clearing delay across banking systems",
                "Missing ledger settlement file",
            ]
            ai_used = False

        # Build financial impact dict
        diff_val = recon.difference_amount if (recon and recon.difference_amount is not None) else Decimal("0")
        currency_val = txn.currency if txn else "INR"
        impact = {
            "amount_difference": float(diff_val),
            "currency": currency_val,
            "ai_synthesized": ai_used,
            "fallback_used": not ai_used,
        }

        return {
            "summary": summary,
            "confirmed_facts": confirmed_facts,
            "possible_causes": possible_causes,
            "root_cause": root_cause,
            "recommended_action": recommended_action,
            "impact": impact,
            "ai_used": ai_used,
        }

    async def run_investigation(
        self,
        exception_id: Optional[uuid.UUID] = None,
        reconciliation_id: Optional[uuid.UUID] = None,
        force: bool = False,
        current_user: Optional[User] = None,
    ) -> AgentInvestigation:
        """
        High-level investigation workflow:
          1. Check duplicate completed investigation unless force=True
          2. Collect evidence
          3. Run deterministic decision engine
          4. Synthesize explanations via AI or fallback
          5. Generate escalation recommendation if required
          6. Persist AgentInvestigation and write audit logs
        """
        start_time = time.time()

        # Step 1: Duplicate prevention check
        if not force:
            existing = self._find_existing_investigation(exception_id, reconciliation_id)
            if existing and existing.status == InvestigationStatus.completed:
                logger.info(
                    "Reusing existing completed investigation %s for exception=%s recon=%s",
                    existing.id,
                    exception_id,
                    reconciliation_id,
                )
                return existing

        # Create new initial pending/investigating record
        inv = AgentInvestigation(
            id=uuid.uuid4(),
            reconciliation_id=reconciliation_id,
            exception_id=exception_id,
            status=InvestigationStatus.investigating,
            investigation_type="general_investigation",
            summary="Investigation initiated by AI Reconciliation Agent.",
            confirmed_facts=[],
            possible_causes=[],
            impact={},
            decision=AgentDecision.review,
            risk_level=RiskLevel.medium,
            evidence=[],
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(inv)
        self.db.commit()
        self.db.refresh(inv)

        # Audit: investigation_started
        user_id = current_user.id if current_user else None
        audit_service.create_audit_log(
            self.db,
            action="investigation_started",
            user_id=user_id,
            entity_type="agent_investigation",
            entity_id=str(inv.id),
            details={
                "exception_id": str(exception_id) if exception_id else None,
                "reconciliation_id": str(reconciliation_id) if reconciliation_id else None,
                "force": force,
            },
        )
        log_investigation_event(
            "investigation_started",
            investigation_id=inv.id,
            exception_id=exception_id,
            reconciliation_id=reconciliation_id,
        )

        try:
            # Step 2: Collect evidence
            context = self.collect_evidence(
                exception_id=exception_id,
                reconciliation_id=reconciliation_id,
            )
            # Update foreign keys if discovered via link
            if not inv.reconciliation_id and context.reconciliation_result:
                inv.reconciliation_id = context.reconciliation_result.id
            if not inv.exception_id and context.exception:
                inv.exception_id = context.exception.id

            inv.evidence = context.evidence
            recon_match = context.reconciliation_result.match_status.value if context.reconciliation_result else "unresolved"
            inv.investigation_type = recon_match

            # Audit: evidence_collected
            audit_service.create_audit_log(
                self.db,
                action="evidence_collected",
                user_id=user_id,
                entity_type="agent_investigation",
                entity_id=str(inv.id),
                details={"evidence_count": len(context.evidence), "investigation_type": inv.investigation_type},
            )

            # Step 3: Run deterministic decision rules
            decision_outcome = self.make_decision(context)
            inv.decision = decision_outcome.decision
            inv.risk_level = decision_outcome.risk_level
            inv.confidence_score = decision_outcome.confidence_score
            inv.escalation_required = decision_outcome.escalation_required

            # Step 4: Synthesize explanations via AI or fallback
            synthesis = await self.analyze_evidence(context)
            inv.summary = synthesis["summary"]
            inv.confirmed_facts = synthesis["confirmed_facts"]
            inv.possible_causes = synthesis["possible_causes"]
            inv.root_cause = synthesis["root_cause"]
            inv.recommended_action = synthesis["recommended_action"]
            inv.impact = synthesis["impact"]

            # Step 5: Escalation recommendations if required
            if inv.escalation_required:
                escalation = self.escalation_service.generate_recommendation(
                    context=context,
                    decision_rationale=decision_outcome.rationale,
                )
                inv.escalation_team = escalation.recommended_team

                audit_service.create_audit_log(
                    self.db,
                    action="escalation_created",
                    user_id=user_id,
                    entity_type="agent_investigation",
                    entity_id=str(inv.id),
                    details={
                        "team": escalation.recommended_team,
                        "priority": escalation.priority,
                        "reason": escalation.reason,
                    },
                )

            inv.status = InvestigationStatus.completed
            inv.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(inv)

            duration = (time.time() - start_time) * 1000.0
            audit_service.create_audit_log(
                self.db,
                action="investigation_completed",
                user_id=user_id,
                entity_type="agent_investigation",
                entity_id=str(inv.id),
                details={"decision": inv.decision.value, "duration_ms": duration},
            )
            log_investigation_event(
                "investigation_completed",
                investigation_id=inv.id,
                exception_id=inv.exception_id,
                reconciliation_id=inv.reconciliation_id,
                status=inv.status.value,
                decision=inv.decision.value,
                duration_ms=duration,
            )
            return inv

        except Exception as exc_err:
            try:
                self.db.rollback()
                failed_inv = self.db.query(AgentInvestigation).filter(AgentInvestigation.id == inv.id).first()
                if not failed_inv:
                    failed_inv = inv
                    self.db.add(failed_inv)
                failed_inv.status = InvestigationStatus.failed
                failed_inv.summary = f"Investigation failed: {str(exc_err)}"
                failed_inv.completed_at = datetime.now(timezone.utc)
                self.db.commit()
            except Exception:
                pass

            duration = (time.time() - start_time) * 1000.0
            audit_service.create_audit_log(
                self.db,
                action="investigation_failed",
                user_id=user_id,
                entity_type="agent_investigation",
                entity_id=str(inv.id),
                details={"error": str(exc_err), "duration_ms": duration},
            )
            log_investigation_event(
                "investigation_failed",
                investigation_id=inv.id,
                exception_id=inv.exception_id,
                reconciliation_id=inv.reconciliation_id,
                status="failed",
                duration_ms=duration,
                details={"error": str(exc_err)},
            )
            raise

    def _find_existing_investigation(
        self,
        exception_id: Optional[uuid.UUID],
        reconciliation_id: Optional[uuid.UUID],
    ) -> Optional[AgentInvestigation]:
        """Finds most recent completed investigation for the target entity."""
        query = self.db.query(AgentInvestigation)
        if exception_id:
            query = query.filter(AgentInvestigation.exception_id == exception_id)
        elif reconciliation_id:
            query = query.filter(AgentInvestigation.reconciliation_id == reconciliation_id)
        else:
            return None
        return query.order_by(AgentInvestigation.created_at.desc()).first()

    # Aliases for explicit API signatures
    async def investigate_exception(
        self,
        exception_id: uuid.UUID,
        force: bool = False,
        current_user: Optional[User] = None,
    ) -> AgentInvestigation:
        return await self.run_investigation(
            exception_id=exception_id,
            force=force,
            current_user=current_user,
        )

    async def investigate_reconciliation(
        self,
        reconciliation_id: uuid.UUID,
        force: bool = False,
        current_user: Optional[User] = None,
    ) -> AgentInvestigation:
        return await self.run_investigation(
            reconciliation_id=reconciliation_id,
            force=force,
            current_user=current_user,
        )
