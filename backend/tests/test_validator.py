"""Unit tests for the mechanical claim validator."""

from __future__ import annotations

from app.common.validator import validate_claim, ClaimResult, ClaimStatus


class TestValidator:
    def test_value_present_supported(self):
        """Value in evidence + no metadata → SUPPORTED."""
        result = validate_claim(
            value=2644,
            unit=None,
            entity=None,
            period=None,
            evidence_text="ECL 31.3.84 2,644 10,343",
            document_id="doc",
            page_range="1-3",
        )
        assert result.status == ClaimStatus.SUPPORTED

    def test_value_unit_entity_period_all_present_supported(self):
        """All fields present and matching → SUPPORTED."""
        result = validate_claim(
            value=2644,
            unit="persons",
            entity="ECL",
            period="31.3.84",
            evidence_text="ECL 31.3.84 2,644 personnel",
            document_id="doc",
            page_range="1-3",
        )
        assert result.status == ClaimStatus.SUPPORTED

    def test_value_missing_unsupported(self):
        """Value not in evidence → UNSUPPORTED."""
        result = validate_claim(
            value=99999,
            unit=None,
            entity=None,
            period=None,
            evidence_text="ECL 31.3.84 2,644",
            document_id="doc",
            page_range="1-3",
        )
        assert result.status == ClaimStatus.UNSUPPORTED

    def test_value_ok_unit_missing_needs_review(self):
        """Value matches but unit not in evidence → NEEDS_REVIEW."""
        result = validate_claim(
            value=2644,
            unit="tonnes",
            entity=None,
            period=None,
            evidence_text="ECL 31.3.84 2,644 personnel",
            document_id="doc",
            page_range="1-3",
        )
        assert result.status == ClaimStatus.NEEDS_REVIEW

    def test_value_ok_entity_missing_needs_review(self):
        """Value matches but entity not in evidence → NEEDS_REVIEW."""
        result = validate_claim(
            value=2644,
            unit="persons",
            entity="BCCL",  # wrong entity
            period=None,
            evidence_text="ECL 31.3.84 2,644 personnel",
            document_id="doc",
            page_range="1-3",
        )
        assert result.status == ClaimStatus.NEEDS_REVIEW

    def test_value_ok_period_missing_needs_review(self):
        """Value matches but period not in evidence → NEEDS_REVIEW."""
        result = validate_claim(
            value=2644,
            unit="persons",
            entity="ECL",
            period="31.3.85",  # wrong period
            evidence_text="ECL 31.3.84 2,644 personnel",
            document_id="doc",
            page_range="1-3",
        )
        assert result.status == ClaimStatus.NEEDS_REVIEW

    def test_missing_document_id_unsupported(self):
        """No document_id → UNSUPPORTED."""
        result = validate_claim(
            value=2644,
            unit=None,
            entity=None,
            period=None,
            evidence_text="ECL 31.3.84 2,644 personnel",
            document_id="",
            page_range="1-3",
        )
        assert result.status == ClaimStatus.UNSUPPORTED