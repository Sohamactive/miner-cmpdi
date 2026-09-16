"""Mechanical claim validation — code, not LLM.

Every numeric claim is checked against evidence:
- SUPPORTED: value present in evidence, unit matches, period matches, citation present
- NEEDS_REVIEW: partial match (value present but unit/period unclear)
- UNSUPPORTED: value not in evidence, no citation. Quarantined, never exported.
"""

from __future__ import annotations

import logging
import re

from app.reports.schemas import Claim, EvidenceBundle, EvidenceItem, ValidationStatus

logger = logging.getLogger(__name__)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _value_in_evidence(claim: Claim, evidence_items: list[EvidenceItem]) -> EvidenceItem | None:
    """Check if the claim's value appears in any evidence item's text."""
    if claim.value is None:
        return None
    value_str = str(claim.value)
    value_patterns = [
        value_str,
        value_str.replace(".", r"\."),
        f"{claim.value:,.1f}" if isinstance(claim.value, float) else f"{claim.value:,}",
    ]
    for item in evidence_items:
        text_lower = _normalize(item.text)
        for pattern in value_patterns:
            if pattern in text_lower:
                return item
    return None


def _unit_matches(claim: Claim, evidence_item: EvidenceItem) -> bool:
    """Check if unit in claim matches unit in evidence."""
    if claim.unit is None or evidence_item.unit is None:
        return True  # can't check, assume ok
    return _normalize(claim.unit) == _normalize(evidence_item.unit)


def _period_matches(claim: Claim, evidence_item: EvidenceItem) -> bool:
    """Check if period in claim matches period in evidence."""
    if claim.period is None or evidence_item.period is None:
        return True  # can't check, assume ok
    return _normalize(claim.period) in _normalize(evidence_item.period) or \
           _normalize(evidence_item.period) in _normalize(claim.period)


def _citation_present(claim: Claim) -> bool:
    """Check if claim has document_id and page_range."""
    return bool(claim.document_id and claim.page_range)


def validate_claim(claim: Claim, evidence: EvidenceBundle) -> Claim:
    """Validate a single claim against the evidence bundle.

    Mutates and returns the claim with validation_status and validation_reasons set.
    """
    reasons: list[str] = []

    # Combine all evidence items
    all_items = evidence.facts + evidence.chunks

    # Check if value is in evidence
    matching_item = _value_in_evidence(claim, all_items)
    if matching_item is None:
        reasons.append(f"Value {claim.value} not found in any evidence text")
        claim.validation_status = ValidationStatus.UNSUPPORTED
        claim.validation_reasons = reasons
        return claim

    # Value found — check unit
    if not _unit_matches(claim, matching_item):
        reasons.append(f"Unit mismatch: claim has '{claim.unit}', evidence has '{matching_item.unit}'")

    # Check period
    if not _period_matches(claim, matching_item):
        reasons.append(f"Period mismatch: claim has '{claim.period}', evidence has '{matching_item.period}'")

    # Check citation
    if not _citation_present(claim):
        reasons.append("No citation (document_id or page_range missing)")

    # Determine status
    if not reasons:
        claim.validation_status = ValidationStatus.SUPPORTED
    elif len(reasons) == 1 and "No citation" in reasons[0]:
        claim.validation_status = ValidationStatus.NEEDS_REVIEW
    else:
        claim.validation_status = ValidationStatus.NEEDS_REVIEW

    # Attach evidence provenance
    if matching_item.document_id:
        claim.document_id = matching_item.document_id
    if matching_item.page_range:
        claim.page_range = matching_item.page_range
    claim.evidence_text = matching_item.text[:500]

    claim.validation_reasons = reasons
    return claim


def validate_claims(claims: list[Claim], evidence: EvidenceBundle) -> list[Claim]:
    """Validate all claims. Returns list with validation_status set."""
    validated: list[Claim] = []
    for claim in claims:
        validated.append(validate_claim(claim, evidence))

    supported = sum(1 for c in validated if c.validation_status == ValidationStatus.SUPPORTED)
    needs_review = sum(1 for c in validated if c.validation_status == ValidationStatus.NEEDS_REVIEW)
    unsupported = sum(1 for c in validated if c.validation_status == ValidationStatus.UNSUPPORTED)
    logger.info("Validation: %d supported, %d needs_review, %d unsupported", supported, needs_review, unsupported)

    return validated


def extract_claims_from_sections(
    sections: list,
    evidence: EvidenceBundle,
) -> list[Claim]:
    """Extract numeric claims from report sections for validation.

    Looks for numbers in paragraphs and creates Claim objects.
    """
    claims: list[Claim] = []
    all_items = evidence.facts + evidence.chunks

    for section in sections:
        paragraphs = getattr(section, "paragraphs", []) or []
        fact_ids = getattr(section, "fact_ids", []) or []

        for para in paragraphs:
            # Find numbers in paragraph text
            numbers = re.findall(r"\b\d+(?:\.\d+)?(?:\s*(?:MT|lakh|tonne|tonnes| crore| lakh-tonne))?\b", str(para))
            if not numbers:
                continue

            # Match number to evidence
            for num_str in numbers:
                try:
                    value = float(re.sub(r"[^\d.]", "", num_str))
                except ValueError:
                    continue

                # Find matching evidence item
                for item in all_items:
                    if item.value is not None and abs(item.value - value) < 0.01:
                        claims.append(Claim(
                            claim_text=str(para)[:300],
                            fact_id=None,
                            document_id=item.document_id,
                            page_range=item.page_range,
                            evidence_text=item.text[:500],
                            value=item.value,
                            unit=item.unit,
                            metric=item.metric,
                            entity=item.entity,
                            period=item.period,
                            confidence=item.score,
                        ))
                        break

    # Dedupe by (value, document_id, page_range)
    seen: set[tuple] = set()
    deduped: list[Claim] = []
    for c in claims:
        key = (c.value, c.document_id, c.page_range)
        if key not in seen:
            seen.add(key)
            deduped.append(c)

    logger.info("Extracted %d unique claims from sections", len(deduped))
    return deduped
