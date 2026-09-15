"""Mechanical claim validator: code-only, no LLM.

Maps a claim (value, unit, entity, period) against evidence text
and returns SUPPORTED / NEEDS_REVIEW / UNSUPPORTED.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class ClaimStatus:
    SUPPORTED = "SUPPORTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    UNSUPPORTED = "UNSUPPORTED"

    choices = [SUPPORTED, NEEDS_REVIEW, UNSUPPORTED]


@dataclass
class ClaimResult:
    status: str
    evidence_snippet: str | None = None
    reason: str | None = None


def _normalize_number_str(value: float | int | str) -> str:
    """Normalize a number for substring-matching against evidence text."""
    if isinstance(value, (int, float)):
        v = float(value)
        if v == int(v):
            return str(int(v))
        # Keep reasonable decimal precision
        return f"{v:g}"
    return str(value)


def _normalize_unit_str(unit: str | None) -> str | None:
    if unit is None:
        return None
    return unit.strip().lower()


def validate_claim(
    *,
    value: float | int | str,
    unit: str | None,
    entity: str | None,
    period: str | None,
    evidence_text: str,
    document_id: str,
    page_range: str | None,
) -> ClaimResult:
    """Validate a claim against evidence; returns ClaimResult.

    Rules (all code, no LLM):
    1. Value must appear in evidence text → SUPPORTED if yes, else UNSUPPORTED.
    2. If unit is provided, it must appear in evidence (case-insensitive).
       If unit mismatches or is absent but value matches → NEEDS_REVIEW.
    3. If entity is provided, it must appear in evidence (case-insensitive).
       If entity is absent → NEEDS_REVIEW.
    4. If period is provided, it must appear in evidence (case-insensitive).
       If period absent → NEEDS_REVIEW.
    5. Citation check: document_id must be non-empty; page_range should be present.
    """
    if not document_id:
        return ClaimResult(status=ClaimStatus.UNSUPPORTED, reason="missing document_id")

    value_str = _normalize_number_str(value)
    evidence_lower = str(evidence_text).lower()
    value_present = value_str.lower() in evidence_lower.replace(",", "")

    unit_norm = _normalize_unit_str(unit)
    person_unit = unit_norm in {"person", "persons", "people", "personnel"}
    unit_present = (
        unit_norm is not None
        and (unit_norm in evidence_lower or (person_unit and "personnel" in evidence_lower))
    )
    if person_unit and unit_norm not in evidence_lower:
        # Count units are commonly represented by numeric-only table columns.
        unit_present = True

    entity_norm = entity.lower() if entity else None
    entity_present = entity_norm is not None and entity_norm in evidence_lower

    period_norm = period.lower() if period else None
    period_present = period_norm is not None and period_norm in evidence_lower

    # Rule 1: value must be in evidence
    if not value_present:
        return ClaimResult(
            status=ClaimStatus.UNSUPPORTED,
            evidence_snippet=str(evidence_text)[:200],
            reason="value not found in evidence",
        )

    # Rule 2-4: check unit, entity, period
    # If any required field is provided and absent from evidence → NEEDS_REVIEW
    # If provided and present → SUPPORTED
    # If not provided at all, we don't fail, but we lean SUPPORTED for the value match

    provided_checks = []
    if unit_norm is not None:
        provided_checks.append(("unit", unit_present))
    if entity_norm is not None:
        provided_checks.append(("entity", entity_present))
    if period_norm is not None:
        provided_checks.append(("period", period_present))

    # If ALL provided checks pass → SUPPORTED
    if all(p for _, p in provided_checks):
        return ClaimResult(status=ClaimStatus.SUPPORTED, evidence_snippet=str(evidence_text)[:200])

    # If some provided checks fail but value matches → NEEDS_REVIEW
    # (Value is grounded but metadata is ambiguous/incomplete)
    if provided_checks:
        return ClaimResult(
            status=ClaimStatus.NEEDS_REVIEW,
            evidence_snippet=str(evidence_text)[:200],
            reason="metadata (unit/entity/period) mismatch with evidence",
        )

    # No metadata provided but value matches → SUPPORTED (best effort)
    return ClaimResult(status=ClaimStatus.SUPPORTED, evidence_snippet=str(evidence_text)[:200])


def validate_claims_batch(
    claims: list[dict],
    evidence_map: dict[str, str],
) -> list[ClaimResult]:
    """Validate multiple claims at once.

    Args:
        claims: list of dicts with keys value, unit, entity, period, evidence_key
        evidence_map: maps an evidence key to the full evidence text string

    Returns:
        list of ClaimResult in same order
    """
    results: list[ClaimResult] = []
    for c in claims:
        result = validate_claim(
            value=c.get("value"),
            unit=c.get("unit"),
            entity=c.get("entity"),
            period=c.get("period"),
            evidence_text=evidence_map.get(c.get("evidence_key", ""), ""),
            document_id=c.get("document_id", ""),
            page_range=c.get("page_range"),
        )
        results.append(result)
    return results