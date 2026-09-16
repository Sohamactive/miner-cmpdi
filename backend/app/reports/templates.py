"""Template and style registry for report generation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SectionSlot:
    name: str
    kind: str  # "text", "fact_table", "chart", "citations"
    required: bool = True


@dataclass(frozen=True)
class ReportTemplate:
    template_id: str
    title: str
    description: str
    sections: list[SectionSlot]
    style: dict[str, str] = field(default_factory=dict)


TEMPLATES: dict[str, ReportTemplate] = {}


def _register(t: ReportTemplate) -> None:
    TEMPLATES[t.template_id] = t


_register(ReportTemplate(
    template_id="parliamentary_reply",
    title="Parliamentary Reply Draft",
    description="Standard reply to parliamentary/administrative coal inquiries with citations.",
    sections=[
        SectionSlot("preamble", "text"),
        SectionSlot("facts_summary", "text"),
        SectionSlot("evidence_table", "fact_table"),
        SectionSlot("production_chart", "chart", required=False),
        SectionSlot("analysis", "text"),
        SectionSlot("conclusion", "text"),
        SectionSlot("citations", "citations"),
    ],
    style={"font": "Calibri", "heading_color": "#1B4F72"},
))

_register(ReportTemplate(
    template_id="geological_summary",
    title="Geological & Mining Summary",
    description="Geological data, production figures, and operational summary.",
    sections=[
        SectionSlot("overview", "text"),
        SectionSlot("geological_data", "text"),
        SectionSlot("production_figures", "fact_table"),
        SectionSlot("trend_chart", "chart", required=False),
        SectionSlot("recommendations", "text"),
        SectionSlot("citations", "citations"),
    ],
    style={"font": "Calibri", "heading_color": "#1A5276"},
))


def get_template(template_id: str) -> ReportTemplate | None:
    return TEMPLATES.get(template_id)


def validate_custom_sections(custom: list[str], template: ReportTemplate) -> list[str] | None:
    """Return list of validation errors if custom sections are invalid, else None."""
    allowed = {slot.name for slot in template.sections}
    errors = []
    for name in custom:
        if name not in allowed:
            errors.append(f"Unknown section '{name}' for template '{template.template_id}'. Allowed: {sorted(allowed)}")
    return errors if errors else None


def section_names(template: ReportTemplate) -> list[str]:
    return [slot.name for slot in template.sections]
