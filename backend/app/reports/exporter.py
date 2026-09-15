"""DOCX export — cover page, headings, fact tables, chart placeholders, citations."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from app.extraction.postgres import create_session
from app.extraction.models import ClaimRecord, Report

logger = logging.getLogger(__name__)

EXPORT_FOLDER = os.getenv("EXPORT_FOLDER", "data/reports")


def _ensure_export_dir() -> Path:
    p = Path(EXPORT_FOLDER)
    p.mkdir(parents=True, exist_ok=True)
    return p


def export_docx(*, report_id: int) -> str:
    """Export a report to DOCX. Returns file path."""
    try:
        from docx import Document as WordDocument
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        raise RuntimeError("python-docx not installed. Run: uv add python-docx")

    session = create_session()
    try:
        report = session.get(Report, report_id)
        if report is None:
            raise ValueError(f"Report {report_id} not found")

        claims = list(session.scalars(
            __import__("sqlalchemy").select(ClaimRecord).where(ClaimRecord.report_id == report_id)
        ))
    finally:
        session.close()

    sections = json.loads(report.sections_json or "[]")
    export_dir = _ensure_export_dir()
    filepath = str(export_dir / f"report-{report_id}.docx")

    doc = WordDocument()

    # Cover page
    style = doc.styles["Title"]
    style.font.size = Pt(24)
    doc.add_paragraph(report.title, style="Title")
    doc.add_paragraph(f"Report Type: {report.report_type.replace('_', ' ').title()}")
    doc.add_paragraph(f"Version: {report.version}")
    doc.add_paragraph("")

    # Table of contents placeholder
    doc.add_heading("Table of Contents", level=1)
    doc.add_paragraph("[TOC — will be updated on open in Word]")
    doc.add_paragraph("")

    # Sections
    for section_data in sections:
        heading = section_data.get("heading", "Untitled")
        paragraphs = section_data.get("paragraphs", [])

        doc.add_heading(heading.replace("_", " ").title(), level=1)

        for para_text in paragraphs:
            doc.add_paragraph(str(para_text))

        # Fact table if present
        fact_table = section_data.get("fact_table")
        if fact_table and isinstance(fact_table, list) and len(fact_table) > 1:
            table = doc.add_table(rows=len(fact_table), cols=len(fact_table[0]))
            table.style = "Table Grid"
            for i, row_data in enumerate(fact_table):
                for j, cell_text in enumerate(row_data):
                    cell = table.cell(i, j)
                    cell.text = str(cell_text)
                    if i == 0:
                        for run in cell.paragraphs[0].runs:
                            run.bold = True
            doc.add_paragraph("")

        # Chart placeholder
        chart_spec = section_data.get("chart_spec")
        if chart_spec:
            doc.add_paragraph(f"[Chart: {chart_spec.get('type', 'bar')} — {chart_spec.get('x_metric', '')} vs {chart_spec.get('y_metric', '')}]")
            doc.add_paragraph("")

    # Citations section
    citations = [c for c in claims if c.validation_status != "UNSUPPORTED"]
    if citations:
        doc.add_heading("Citations", level=1)
        seen: set[str] = set()
        idx = 0
        for c in citations:
            key = f"{c.document_id}:{c.page_range}"
            if key in seen:
                continue
            seen.add(key)
            idx += 1
            doc.add_paragraph(f"[{idx}] Document {c.document_id}, Page {c.page_range} — {c.evidence_text[:200]}")

    # Review summary
    doc.add_heading("Review Summary", level=1)
    supported = sum(1 for c in claims if c.validation_status == "SUPPORTED")
    needs_review = sum(1 for c in claims if c.validation_status == "NEEDS_REVIEW")
    unsupported = sum(1 for c in claims if c.validation_status == "UNSUPPORTED")
    doc.add_paragraph(f"SUPPORTED: {supported} claims")
    doc.add_paragraph(f"NEEDS_REVIEW: {needs_review} claims")
    doc.add_paragraph(f"UNSUPPORTED: {unsupported} claims (quarantined)")

    doc.save(filepath)
    logger.info("DOCX exported: %s (report_id=%d)", filepath, report_id)
    return filepath
