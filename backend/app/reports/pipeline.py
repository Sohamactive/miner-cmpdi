"""Report pipeline orchestrator — gather → draft → validate → assemble → HITL loop.

Ported from SOW pipeline.py pattern with human-in-loop revision.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable

from sqlalchemy import select

from app.extraction.postgres import create_session
from app.extraction.models import ClaimRecord, Report
from app.reports.retrieval import gather_evidence
from app.reports.writer import write_sections
from app.reports.validate import extract_claims_from_sections, validate_claims
from app.reports.assembler import assemble_sections
from app.reports.templates import get_template, section_names

logger = logging.getLogger(__name__)

MAX_REVISIONS = 5
REPORT_TIMEOUT_S = 600


class ReportPipeline:
    """Orchestrates report generation with HITL revision loop."""

    def run(
        self,
        *,
        question: str,
        report_type: str = "parliamentary_reply",
        custom_sections: list[str] | None = None,
        doc_ids: list[str] | None = None,
        title: str = "",
        progress_callback: Callable[[int, str], None] | None = None,
    ) -> dict:
        """Full pipeline: gather → draft → validate → assemble → needs_review."""
        start_time = time.time()

        template = get_template(report_type)
        if template is None:
            raise ValueError(f"Unknown report type: {report_type}")

        def notify(step: int, label: str) -> None:
            if progress_callback:
                progress_callback(step, label)

        # Phase 1: Gather evidence
        notify(0, "Gathering evidence")
        evidence = gather_evidence(question=question, doc_ids=doc_ids)

        # Phase 2: Draft sections
        notify(1, "Drafting sections")
        sections = write_sections(
            question=question,
            title=title or template.title,
            template=template,
            evidence=evidence,
            custom_sections=custom_sections,
        )

        # Phase 2b: Extract and validate claims
        notify(2, "Validating claims")
        claims = extract_claims_from_sections(sections, evidence)
        claims = validate_claims(claims, evidence)

        # Phase 2c: Assemble
        notify(3, "Assembling report")
        assembled = assemble_sections(sections, claims, evidence)

        # Check if any UNSUPPORTED — flag needs_review
        has_unsupported = any(c.validation_status.value == "UNSUPPORTED" for c in claims)
        status = "needs_review" if has_unsupported else "needs_review"

        # Persist to DB
        notify(4, "Saving report")
        report_id = self._persist(
            report_type=report_type,
            title=title or template.title,
            question=question,
            sections=sections,
            assembled=assembled,
            claims=claims,
        )

        notify(5, "Done")
        logger.info("Pipeline complete: report_id=%d, claims=%d, time=%.1fs",
                     report_id, len(claims), time.time() - start_time)

        return {
            "report_id": report_id,
            "status": status,
            "title": title or template.title,
            "sections": [s.model_dump() for s in sections],
            "claims": [
                {
                    "id": i + 1,
                    "claim_text": c.claim_text,
                    "evidence_text": c.evidence_text,
                    "value": c.value,
                    "unit": c.unit,
                    "validation_status": c.validation_status.value,
                    "confidence": c.confidence,
                }
                for i, c in enumerate(claims)
            ],
            "assembled": assembled,
            "version": 1,
        }

    def revise(
        self,
        *,
        report_id: int,
        feedback_note: str,
        edited_sections: list[dict] | None = None,
    ) -> dict:
        """Revise an existing report based on user feedback (HITL loop)."""
        session = create_session()
        try:
            report = session.get(Report, report_id)
            if report is None:
                raise ValueError(f"Report {report_id} not found")

            # Check revision limit
            if report.version >= MAX_REVISIONS:
                return {"error": f"Maximum revisions ({MAX_REVISIONS}) reached. Please approve or reject."}

            # Get original sections
            old_sections = json.loads(report.sections_json or "[]")
            question = json.loads(report.parameters_json or "{}").get("question", "")

            template = get_template(report.report_type)
            if template is None:
                raise ValueError(f"Unknown report type: {report.report_type}")

            # Re-gather evidence
            evidence = gather_evidence(question=question)

            # Re-draft with feedback
            sections = write_sections(
                question=question,
                title=report.title,
                template=template,
                evidence=evidence,
                feedback_note=feedback_note,
            )

            # Apply any user-edited sections
            if edited_sections:
                edits = {e.get("heading", ""): e for e in edited_sections if isinstance(e, dict)}
                for i, section in enumerate(sections):
                    if section.heading in edits:
                        edit = edits[section.heading]
                        if "paragraphs" in edit:
                            sections[i].paragraphs = edit["paragraphs"]

            # Re-validate
            claims = extract_claims_from_sections(sections, evidence)
            claims = validate_claims(claims, evidence)
            assembled = assemble_sections(sections, claims, evidence)

            # Update DB
            report.version += 1
            report.sections_json = json.dumps([s.model_dump() for s in sections])
            report.parameters_json = json.dumps({
                "question": question,
                "feedback": feedback_note,
                "version": report.version,
            })
            session.commit()

            logger.info("Report %d revised to v%d, claims=%d", report_id, report.version, len(claims))
            return {
                "report_id": report_id,
                "status": "needs_review",
                "title": report.title,
                "sections": [s.model_dump() for s in sections],
                "claims": [
                    {
                        "id": i + 1,
                        "claim_text": c.claim_text,
                        "evidence_text": c.evidence_text,
                        "value": c.value,
                        "unit": c.unit,
                        "validation_status": c.validation_status.value,
                        "confidence": c.confidence,
                    }
                    for i, c in enumerate(claims)
                ],
                "assembled": assembled,
                "version": report.version,
            }
        finally:
            session.close()

    def _persist(
        self,
        *,
        report_type: str,
        title: str,
        question: str,
        sections: list,
        assembled: dict,
        claims: list,
    ) -> int:
        """Save report to PostgreSQL. Returns report_id."""
        session = create_session()
        try:
            report = Report(
                report_type=report_type,
                status="needs_review",
                title=title,
                parameters_json=json.dumps({"question": question}),
                sections_json=json.dumps([s.model_dump() for s in sections]),
                version=1,
            )
            session.add(report)
            session.flush()

            for claim in claims:
                session.add(ClaimRecord(
                    report_id=report.id,
                    claim_text=claim.claim_text,
                    fact_id=claim.fact_id,
                    document_id=claim.document_id,
                    page_range=claim.page_range,
                    evidence_text=claim.evidence_text,
                    value=claim.value,
                    unit=claim.unit,
                    validation_status=claim.validation_status.value,
                    validation_reasons=json.dumps(claim.validation_reasons),
                    confidence=claim.confidence,
                ))

            session.commit()
            return report.id
        finally:
            session.close()
