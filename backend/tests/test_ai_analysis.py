"""
tests/test_ai_analysis.py

Comprehensive tests for Step 6: AI Mismatch Analysis & Exception Investigation.
Covers:
  - Unit tests for prompts, parser, and fallback analyzer
  - AI client timeout, network error, and missing API key handling
  - Mocked external LLM provider
  - All 7 discrepancy categories (amount mismatch, missing in bank, missing in gateway,
    duplicate, delayed, status mismatch, unresolved)
  - API endpoints, authentication, authorization, duplicate prevention, and history
"""

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.ai_analysis import AIAnalysis
from app.models.bank_transaction import BankTransaction
from app.models.enums import (
    AnalysisStatus,
    AnalysisType,
    BankTransactionStatus,
    ExceptionSeverity,
    ExceptionStatus,
    MatchStatus,
    RiskLevel,
    TransactionSource,
    TransactionStatus,
)
from app.models.exception import PaymentException
from app.models.merchant import Merchant
from app.models.reconciliation_result import ReconciliationResult
from app.models.transaction import Transaction
from app.services.ai.ai_client import AIClient, AIAvailabilityError
from app.services.ai.fallback_analyzer import analyze_fallback
from app.services.ai.prompts import build_analysis_prompt
from app.services.ai.recommendation_service import generate_recommendations
from app.services.ai.response_parser import (
    AIResponseParseError,
    clean_llm_json_text,
    parse_ai_response,
)
from app.services.ai.root_cause_analyzer import analyze_root_cause


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_merchant(db: Session, suffix: str = "ai") -> Merchant:
    merchant = Merchant(
        name=f"Merchant {suffix}",
        email=f"merchant_{suffix}_{uuid.uuid4().hex[:6]}@example.com",
        business_name=f"Business {suffix}",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


def _seed_recon_pair(
    db: Session,
    match_status: MatchStatus = MatchStatus.amount_mismatch,
    expected_amount: Decimal = Decimal("5000.00"),
    actual_amount: Decimal = Decimal("4900.00"),
    diff: Decimal = Decimal("100.00"),
    txn_status: TransactionStatus = TransactionStatus.success,
    bank_status: BankTransactionStatus = BankTransactionStatus.posted,
    create_exception: bool = True,
):
    merchant = _seed_merchant(db, f"recon_{uuid.uuid4().hex[:4]}")
    now = datetime.now(timezone.utc)

    gtxn = Transaction(
        transaction_reference=f"TXN-{uuid.uuid4().hex[:6].upper()}",
        order_reference=f"ORD-{uuid.uuid4().hex[:6].upper()}",
        merchant_id=merchant.id,
        amount=expected_amount,
        currency="INR",
        transaction_date=now,
        payment_method="UPI",
        gateway="Razorpay",
        status=txn_status,
        source=TransactionSource.gateway,
    )
    db.add(gtxn)

    btxn = BankTransaction(
        bank_reference=f"BNK-{uuid.uuid4().hex[:6].upper()}",
        transaction_reference=gtxn.transaction_reference,
        amount=actual_amount,
        transaction_date=now,
        bank_name="HDFC Bank",
        status=bank_status.value if hasattr(bank_status, "value") else str(bank_status),
    )
    db.add(btxn)
    db.commit()

    recon = ReconciliationResult(
        transaction_id=gtxn.id,
        bank_transaction_id=btxn.id,
        match_status=match_status,
        confidence_score=Decimal("0.8500"),
        expected_amount=expected_amount,
        actual_amount=actual_amount,
        difference_amount=diff,
        matching_method="Exact Reference",
        explanation="Discrepancy detected during deterministic matching.",
        reconciled_at=now,
    )
    db.add(recon)
    db.commit()
    db.refresh(recon)

    exc = None
    if create_exception:
        exc = PaymentException(
            reconciliation_id=recon.id,
            severity=ExceptionSeverity.high,
            category="amount_mismatch",
            title=f"Discrepancy of INR {diff}",
            description="Expected and actual amounts differ.",
            recommended_action="Review gateway settlement statement.",
            status=ExceptionStatus.open,
        )
        db.add(exc)
        db.commit()
        db.refresh(exc)

    return recon, exc, gtxn, btxn


# ---------------------------------------------------------------------------
# 1. Prompt and Parser Unit Tests
# ---------------------------------------------------------------------------


class TestAIPromptsAndParser:
    def test_prompt_builder_contains_context_and_constraints(self):
        context = {
            "reconciliation": {"match_status": "amount_mismatch", "expected_amount": "5000", "actual_amount": "4900"},
            "transaction": {"transaction_reference": "TXN001", "currency": "INR"},
        }
        prompt = build_analysis_prompt(context, "exception_analysis")
        assert "TXN001" in prompt
        assert "amount_mismatch" in prompt
        assert "SPECIAL INSTRUCTION FOR AMOUNT MISMATCH" in prompt

    def test_clean_markdown_code_fences(self):
        wrapped = "```json\n{\"summary\": \"test\"}\n```"
        cleaned = clean_llm_json_text(wrapped)
        assert cleaned == '{"summary": "test"}'

        plain = '{"summary": "test"}'
        assert clean_llm_json_text(plain) == '{"summary": "test"}'

    def test_parse_valid_ai_response(self):
        raw = json.dumps({
            "summary": "Gateway and bank amounts differ by INR 100.",
            "root_cause": "Possible cause: MDR processing fee deduction.",
            "impact": "Ledger imbalance of INR 100.",
            "recommended_action": "Check settlement batch report.",
            "risk_level": "medium",
            "confidence_score": 0.92,
        })
        parsed = parse_ai_response(raw)
        assert parsed["summary"] == "Gateway and bank amounts differ by INR 100."
        assert parsed["risk_level"] == RiskLevel.medium
        assert parsed["confidence_score"] == Decimal("0.9200")

    def test_parse_invalid_json_raises_error(self):
        with pytest.raises(AIResponseParseError):
            parse_ai_response("This is not valid JSON string.")

    def test_parse_missing_summary_raises_error(self):
        with pytest.raises(AIResponseParseError):
            parse_ai_response(json.dumps({"root_cause": "some cause"}))


# ---------------------------------------------------------------------------
# 2. Fallback Analyzer Unit Tests (All 7 Categories)
# ---------------------------------------------------------------------------


class TestFallbackAnalyzer:
    def test_fallback_amount_mismatch(self):
        ctx = {
            "reconciliation": {"match_status": "amount_mismatch", "expected_amount": "5000", "actual_amount": "4900", "difference_amount": "100"},
            "transaction": {"currency": "INR"},
        }
        res = analyze_fallback(ctx)
        assert res["status"] == AnalysisStatus.fallback
        assert res["ai_provider"] == "fallback"
        assert "Payment amount mismatch" in res["summary"]
        assert "Possible causes (unconfirmed)" in res["root_cause"]
        assert res["risk_level"] == RiskLevel.medium

    def test_fallback_missing_in_bank(self):
        ctx = {
            "reconciliation": {"match_status": "missing_in_bank"},
            "transaction": {"transaction_reference": "TXN_MISSING_1", "currency": "INR"},
        }
        res = analyze_fallback(ctx)
        assert res["status"] == AnalysisStatus.fallback
        assert "no corresponding bank deposit" in res["summary"]
        assert res["risk_level"] == RiskLevel.high

    def test_fallback_missing_in_gateway(self):
        ctx = {
            "reconciliation": {"match_status": "missing_in_gateway"},
            "bank_transaction": {"bank_reference": "BNK_UNMAPPED_1", "amount": "1000", "currency": "INR"},
        }
        res = analyze_fallback(ctx)
        assert "originating gateway payment record" in res["summary"]
        assert res["risk_level"] == RiskLevel.high

    def test_fallback_duplicate(self):
        ctx = {
            "reconciliation": {"match_status": "duplicate"},
            "transaction": {"transaction_reference": "DUP_REF_001"},
        }
        res = analyze_fallback(ctx)
        assert "Duplicate record detected" in res["summary"]
        assert res["risk_level"] == RiskLevel.high

    def test_fallback_delayed(self):
        ctx = {
            "reconciliation": {"match_status": "delayed"},
            "transaction": {"transaction_date": "2026-09-01"},
            "bank_transaction": {"transaction_date": "2026-09-05"},
        }
        res = analyze_fallback(ctx)
        assert "timing delay" in res["summary"]
        assert res["risk_level"] == RiskLevel.low

    def test_fallback_status_mismatch_critical(self):
        ctx = {
            "reconciliation": {"match_status": "unresolved"},
            "transaction": {"status": "success"},
            "bank_transaction": {"status": "failed"},
        }
        res = analyze_fallback(ctx)
        assert "Critical status conflict" in res["summary"]
        assert res["risk_level"] == RiskLevel.critical
        assert "IMMEDIATE HUMAN INVESTIGATION" in res["recommended_action"]

    def test_fallback_unresolved_general(self):
        ctx = {
            "reconciliation": {"match_status": "unresolved"},
        }
        res = analyze_fallback(ctx)
        assert "could not be conclusively determined" in res["summary"]
        assert res["risk_level"] == RiskLevel.medium


# ---------------------------------------------------------------------------
# 3. AI Client & Resilience Unit Tests
# ---------------------------------------------------------------------------


class TestAIClientAndResilience:
    @pytest.mark.asyncio
    async def test_ai_client_missing_key_raises_availability_error(self):
        client = AIClient(api_key="", service_url="")
        with pytest.raises(AIAvailabilityError):
            await client.generate_analysis("Analyze this")

    @pytest.mark.asyncio
    async def test_ai_client_timeout_triggers_availability_error(self):
        import httpx

        client = AIClient(api_key="mock_key", service_url="https://mock.example.com/api")
        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timed out")):
            with pytest.raises(AIAvailabilityError) as exc_info:
                await client.generate_analysis("Analyze this")
            assert "timed out" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_ai_client_network_failure_triggers_availability_error(self):
        import httpx

        client = AIClient(api_key="mock_key", service_url="https://mock.example.com/api")
        with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
            with pytest.raises(AIAvailabilityError) as exc_info:
                await client.generate_analysis("Analyze this")
            assert "Network error" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 4. Service Flow & Sub-Analyzers Tests
# ---------------------------------------------------------------------------


class TestAIServiceSubAnalyzers:
    @pytest.mark.asyncio
    async def test_root_cause_analyzer_runs_successfully(self, session):
        recon, exc, _, _ = _seed_recon_pair(session)
        mock_client = AIClient(api_key="")  # Will fall back safely
        analysis = await analyze_root_cause(
            db=session,
            recon=recon,
            exc=exc,
            force=True,
            ai_client=mock_client,
        )
        assert analysis.analysis_type == AnalysisType.root_cause
        assert analysis.status == AnalysisStatus.fallback

    @pytest.mark.asyncio
    async def test_recommendation_service_runs_successfully(self, session):
        recon, exc, _, _ = _seed_recon_pair(session)
        mock_client = AIClient(api_key="")
        analysis = await generate_recommendations(
            db=session,
            recon=recon,
            exc=exc,
            force=True,
            ai_client=mock_client,
        )
        assert analysis.analysis_type == AnalysisType.recommendation
        assert analysis.recommended_action is not None


# ---------------------------------------------------------------------------
# 5. API Integration Tests
# ---------------------------------------------------------------------------


class TestAIAnalysisAPI:
    def test_unauthenticated_request_returns_401(self, client):
        dummy_id = uuid.uuid4()
        resp = client.post(f"/api/ai/analyze/{dummy_id}")
        assert resp.status_code == 401

    def test_analyze_reconciliation_with_mock_ai_success(self, client, auth_headers, db_session):
        recon, exc, _, _ = _seed_recon_pair(db_session)

        mock_llm_output = json.dumps({
            "summary": "Verified gateway to bank fee deduction.",
            "root_cause": "Possible cause: MDR fee deduction by processor.",
            "impact": "INR 100 settlement variance.",
            "recommended_action": "Match against settlement line items.",
            "risk_level": "medium",
            "confidence_score": 0.94,
        })

        with patch("app.services.ai.ai_client.AIClient.is_configured", True):
            with patch("app.services.ai.ai_client.AIClient.generate_analysis", new=AsyncMock(return_value=mock_llm_output)):
                resp = client.post(
                    f"/api/ai/analyze/{recon.id}",
                    headers=auth_headers,
                )
                assert resp.status_code == 200
                data = resp.json()
                assert data["status"] == "completed"
                assert data["ai_provider"] == "gemini"
                assert data["risk_level"] == "medium"
                assert float(data["confidence_score"]) == 0.94
                assert "Verified gateway to bank fee deduction" in data["summary"]

    def test_analyze_reconciliation_missing_key_uses_fallback(self, client, auth_headers, db_session):
        recon, exc, _, _ = _seed_recon_pair(db_session)

        # Ensure no key is configured
        with patch("app.services.ai.ai_client.AIClient.is_configured", False):
            resp = client.post(
                f"/api/ai/analyze/{recon.id}",
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "fallback"
            assert data["ai_provider"] == "fallback"
            assert "Payment amount mismatch" in data["summary"]

    def test_analyze_exception_endpoint(self, client, auth_headers, db_session):
        recon, exc, _, _ = _seed_recon_pair(db_session)

        with patch("app.services.ai.ai_client.AIClient.is_configured", False):
            resp = client.post(
                f"/api/ai/analyze/exception/{exc.id}",
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["exception_id"] == str(exc.id)
            assert data["status"] == "fallback"

    def test_duplicate_prevention_and_force_reanalysis(self, client, auth_headers, db_session):
        recon, exc, _, _ = _seed_recon_pair(db_session)

        with patch("app.services.ai.ai_client.AIClient.is_configured", False):
            # First call creates record
            r1 = client.post(f"/api/ai/analyze/{recon.id}", headers=auth_headers)
            assert r1.status_code == 200
            id1 = r1.json()["id"]

            # Second call without force=true should return identical record ID
            r2 = client.post(f"/api/ai/analyze/{recon.id}", headers=auth_headers)
            assert r2.status_code == 200
            id2 = r2.json()["id"]
            assert id1 == id2

            # Third call with force=true should produce a new record
            r3 = client.post(f"/api/ai/analyze/{recon.id}?force=true", headers=auth_headers)
            assert r3.status_code == 200
            id3 = r3.json()["id"]
            assert id1 != id3

    def test_deep_investigation_endpoint(self, client, auth_headers, db_session):
        recon, exc, _, _ = _seed_recon_pair(db_session)

        with patch("app.services.ai.ai_client.AIClient.is_configured", False):
            resp = client.post(
                f"/api/ai/investigate/{exc.id}",
                headers=auth_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "analysis" in data
            assert data["investigation_depth"] == "comprehensive"
            assert len(data["discrepancy_factors"]) > 0
            assert len(data["suggested_audit_steps"]) > 0
            assert data["human_action_required"] is True

    def test_list_analyses_with_filters(self, client, auth_headers, db_session):
        recon, exc, _, _ = _seed_recon_pair(db_session)

        with patch("app.services.ai.ai_client.AIClient.is_configured", False):
            client.post(f"/api/ai/analyze/{recon.id}?force=true", headers=auth_headers)

        resp = client.get("/api/ai/analyses", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

        # Test filter by status=fallback
        resp_filter = client.get("/api/ai/analyses?status=fallback", headers=auth_headers)
        assert resp_filter.status_code == 200
        assert all(item["status"] == "fallback" for item in resp_filter.json()["items"])

    def test_get_single_analysis_and_reconciliation_history(self, client, auth_headers, db_session):
        recon, exc, _, _ = _seed_recon_pair(db_session)

        with patch("app.services.ai.ai_client.AIClient.is_configured", False):
            r = client.post(f"/api/ai/analyze/{recon.id}", headers=auth_headers)
            analysis_id = r.json()["id"]

        # Get by ID
        resp = client.get(f"/api/ai/analyses/{analysis_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == analysis_id

        # Get by reconciliation ID
        resp_recon = client.get(f"/api/ai/analyses/reconciliation/{recon.id}", headers=auth_headers)
        assert resp_recon.status_code == 200
        assert len(resp_recon.json()) >= 1

    def test_database_persistence_and_immutability(self, db_session):
        recon, exc, _, _ = _seed_recon_pair(db_session)
        res_fallback = analyze_fallback({"reconciliation": {"match_status": "amount_mismatch"}})

        record = AIAnalysis(
            id=uuid.uuid4(),
            reconciliation_id=recon.id,
            exception_id=exc.id,
            analysis_type=AnalysisType.exception_analysis,
            summary=res_fallback["summary"],
            root_cause=res_fallback["root_cause"],
            impact=res_fallback["impact"],
            recommended_action=res_fallback["recommended_action"],
            risk_level=res_fallback["risk_level"],
            confidence_score=res_fallback["confidence_score"],
            ai_provider="fallback",
            model_name="rule-based-fallback-v1",
            status=AnalysisStatus.fallback,
        )
        db_session.add(record)
        db_session.commit()

        # Check queried record from database
        fetched = db_session.get(AIAnalysis, record.id)
        assert fetched is not None
        assert fetched.summary == res_fallback["summary"]
        assert fetched.reconciliation_result.match_status == MatchStatus.amount_mismatch
        assert fetched.exception.id == exc.id
