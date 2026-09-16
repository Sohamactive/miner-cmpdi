"""Tests for the golden set alignment with validator and QA responder."""

from __future__ import annotations

import json
from datetime import datetime

from app.common.validator import validate_claim, ClaimResult, ClaimStatus
from backend.app.review.qa.models import QAClaim, QAResponse
from app.extraction.postgres import create_session, search_facts, normalize_table_facts
from sqlalchemy import select
from sqlalchemy.orm import Session


def load_golden_set(path: str = "backend/tests/golden_set.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestGoldenSetFacts:
    def test_all_facts_have_required_fields(self, golden_set_path="backend/tests/golden_set.json"):
        """Every fact in the golden set must have entity, metric, period, value, unit."""
        data = load_golden_set(golden_set_path)
        for i, f in enumerate(data["facts"]):
            missing = [k for k in ["entity", "metric", "period", "value", "unit"] if f.get(k) is None]
            assert not missing, f"Fact {i} missing fields: {missing}"

    def test_validator_supports_all_golden_facts(self, golden_set_path="backend/tests/golden_set.json"):
        """Mechanical validator should return SUPPORTED for every golden fact."""
        data = load_golden_set(golden_set_path)
        for fact_data in data["facts"]:
            result = validate_claim(
                value=fact_data["value"],
                unit=fact_data["unit"],
                entity=fact_data["entity"],
                period=fact_data["period"],
                evidence_text=fact_data["evidence_text"],
                document_id=fact_data["document_id"],
                page_range=fact_data["page_range"],
            )
            assert result.status == ClaimStatus.SUPPORTED, (
                f"Fact {fact_data['entity']}/{fact_data['metric']} got {result.status}: {result.reason}"
            )


class TestQAResponse:
    def test_qa_response_has_answer_and_claims(self):
        """A valid QA response must have answer_text and claims list."""
        response = QAResponse(
            answer_text="The executives were 2644 persons.",
            claims=[
                QAClaim(value=2644, unit="persons", document_id="doc", page_range="1-3",
                        evidence_snippet="ECL 31.3.84 2,644", status="SUPPORTED")
            ]
        )
        assert response.answer_text != ""
        assert len(response.claims) > 0
        assert response.claims[0].status in ("SUPPORTED", "NEEDS_REVIEW", "UNSUPPORTED")

    def test_qa_response_validator_alignment(self):
        """QA claims status must be a valid ClaimStatus."""
        response = QAResponse(
            answer_text="Test answer",
            claims=[
                QAClaim(value=2644, unit="persons", document_id="doc", page_range="1-3",
                        evidence_snippet="ECL 31.3.84 2,644", status="INVALID_STATUS")
            ]
        )
        # This should fail because "INVALID_STATUS" is not a valid ClaimStatus
        valid_statuses = {"SUPPORTED", "NEEDS_REVIEW", "UNSUPPORTED"}
        assert response.claims[0].status in valid_statuses