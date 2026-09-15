"""Report assembler — fact tables, matplotlib charts, citation footnotes."""

from __future__ import annotations

import io
import logging
from typing import Any

from app.reports.schemas import Claim, EvidenceBundle, ReportSection, ValidationStatus

logger = logging.getLogger(__name__)


def build_fact_table(claims: list[Claim]) -> list[list[str]]:
    """Build a fact table from validated claims. Only SUPPORTED + NEEDS_REVIEW."""
    header = ["#", "Claim", "Value", "Unit", "Source", "Page", "Status"]
    rows: list[list[str]] = [header]
    idx = 0
    for c in claims:
        if c.validation_status == ValidationStatus.UNSUPPORTED:
            continue
        idx += 1
        rows.append([
            str(idx),
            c.claim_text[:100],
            str(c.value) if c.value is not None else "N/A",
            c.unit or "N/A",
            c.document_id or "N/A",
            c.page_range or "N/A",
            c.validation_status.value,
        ])
    return rows


def build_citations(claims: list[Claim]) -> list[str]:
    """Build citation footnotes from validated claims."""
    citations: list[str] = []
    seen: set[str] = set()
    idx = 0
    for c in claims:
        if c.validation_status == ValidationStatus.UNSUPPORTED:
            continue
        key = f"{c.document_id}:{c.page_range}"
        if key in seen:
            continue
        seen.add(key)
        idx += 1
        citations.append(f"[{idx}] Document {c.document_id}, Page {c.page_range} — {c.evidence_text[:100]}")
    return citations


def build_chart_placeholder(section: ReportSection, evidence: EvidenceBundle) -> dict[str, Any] | None:
    """Return chart spec if section requests one, else None.

    In Phase 3, this will generate matplotlib PNG.
    For now, returns the spec for downstream rendering.
    """
    if section.chart_spec is None:
        return None
    return section.chart_spec


def assemble_sections(
    sections: list[ReportSection],
    claims: list[Claim],
    evidence: EvidenceBundle,
) -> dict[str, Any]:
    """Assemble final report sections with tables, charts, and citations.

    Returns structured dict ready for DOCX export.
    """
    assembled: dict[str, Any] = {}

    for section in sections:
        heading = section.heading
        content: dict[str, Any] = {
            "paragraphs": list(section.paragraphs),
        }

        # Add fact table if this is a table section
        if heading in ("evidence_table", "production_figures", "facts_summary"):
            table = build_fact_table(claims)
            if len(table) > 1:  # more than just header
                content["fact_table"] = table

        # Add chart spec if present
        chart = build_chart_placeholder(section, evidence)
        if chart is not None:
            content["chart_spec"] = chart

        assembled[heading] = content

    # Add citations as last section
    citations = build_citations(claims)
    if citations:
        assembled["citations"] = {"paragraphs": citations}

    logger.info("Assembled %d sections with %d claims", len(assembled), len(claims))
    return assembled
