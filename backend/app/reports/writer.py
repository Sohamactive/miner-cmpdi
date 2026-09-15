"""LLM report writer — drafts sections from evidence bundle + template."""

from __future__ import annotations

import json
import logging

from app.common.llm_client import generate_json
from app.reports.schemas import EvidenceBundle, ReportSection
from app.reports.templates import ReportTemplate, section_names

logger = logging.getLogger(__name__)

WRITER_PROMPT = """You are a mining/coal report writer for CMPDI/CIL.

Using the evidence below and the template sections, write each section of the report.
Every numeric claim MUST reference the evidence provided. Do NOT invent numbers.

Template sections: {sections}
Report title: {title}
User question: {question}

Evidence:
{evidence}

{feedback}

Return JSON only:
{{
  "sections": [
    {{"heading": "section_name", "paragraphs": ["paragraph1", "paragraph2"], "fact_ids": ["fact_ref1"], "chart_spec": null}}
  ]
}}

Rules:
- Each paragraph must be grounded in the evidence provided.
- Include fact_ids (references to evidence items) for any numeric claim.
- chart_spec can be {{"type": "bar", "x_metric": "year", "y_metric": "production"}} or null.
- Do NOT add sections not in the template list.
- If evidence is insufficient, write "Data not available" for that section.
"""

MAX_INPUT_CHARS = 30000


def _format_evidence(bundle: EvidenceBundle) -> str:
    parts: list[str] = []
    for i, item in enumerate(bundle.facts):
        ref = f"[F{i}]"
        loc = f"doc={item.document_id}, page={item.page_range}" if item.page_range else f"doc={item.document_id}"
        val = f" value={item.value} {item.unit}" if item.value is not None else ""
        parts.append(f"{ref} {item.text} ({loc}){val}")
    for i, item in enumerate(bundle.chunks):
        ref = f"[C{i}]"
        loc = f"doc={item.document_id}, page={item.page_range}" if item.page_range else f"doc={item.document_id}"
        parts.append(f"{ref} {item.text[:500]} ({loc})")
    return "\n".join(parts)


def write_sections(
    *,
    question: str,
    title: str,
    template: ReportTemplate,
    evidence: EvidenceBundle,
    feedback_note: str = "",
    custom_sections: list[str] | None = None,
) -> list[ReportSection]:
    """Draft report sections from evidence bundle using LLM."""
    sections = custom_sections or section_names(template)
    evidence_text = _format_evidence(evidence)

    feedback_block = ""
    if feedback_note:
        feedback_block = f"User feedback (address in this revision):\n{feedback_note}"

    prompt = WRITER_PROMPT.format(
        sections=json.dumps(sections),
        title=title or "Mining Report",
        question=question or "General report",
        evidence=evidence_text[:MAX_INPUT_CHARS],
        feedback=feedback_block,
    )

    logger.info("Writer LLM request: %d sections, %d evidence items", len(sections), len(evidence.facts) + len(evidence.chunks))
    result = generate_json(prompt)

    raw_sections = result.get("sections", [])
    if not isinstance(raw_sections, list):
        logger.warning("LLM returned non-list sections, wrapping")
        raw_sections = []

    parsed: list[ReportSection] = []
    for s in raw_sections:
        if not isinstance(s, dict):
            continue
        parsed.append(ReportSection(
            heading=str(s.get("heading", "")),
            paragraphs=[str(p) for p in s.get("paragraphs", []) if isinstance(p, str)],
            fact_ids=[str(f) for f in s.get("fact_ids", []) if isinstance(f, str)],
            chart_spec=s.get("chart_spec") if isinstance(s.get("chart_spec"), dict) else None,
        ))

    # Ensure all template sections are present
    existing = {p.heading for p in parsed}
    for name in sections:
        if name not in existing:
            parsed.append(ReportSection(heading=name, paragraphs=["Data not available."]))

    logger.info("Writer produced %d sections", len(parsed))
    return parsed
