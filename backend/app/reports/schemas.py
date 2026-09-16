"""Pydantic models for the report generation pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    UNSUPPORTED = "UNSUPPORTED"


class ReviewAction(str, Enum):
    APPROVE = "APPROVE"
    EDIT = "EDIT"
    REJECT = "REJECT"


class ReportType(str, Enum):
    PARLIAMENTARY_REPLY = "parliamentary_reply"
    GEOLOGICAL_SUMMARY = "geological_summary"


class ReportStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    EXPORTED = "exported"
    FAILED = "failed"


class EvidenceItem(BaseModel):
    source: str  # "fact" or "chunk"
    document_id: str
    filename: str = ""
    page_range: str | None = None
    text: str
    value: float | None = None
    unit: str | None = None
    metric: str | None = None
    entity: str | None = None
    period: str | None = None
    score: float = 0.0


class CoverageWarning(BaseModel):
    topic: str
    message: str


class EvidenceBundle(BaseModel):
    facts: list[EvidenceItem] = []
    chunks: list[EvidenceItem] = []
    coverage_warnings: list[CoverageWarning] = []


class Claim(BaseModel):
    claim_id: str = ""
    claim_text: str
    fact_id: int | None = None
    document_id: str | None = None
    page_range: str | None = None
    evidence_text: str = ""
    value: float | None = None
    unit: str | None = None
    metric: str | None = None
    entity: str | None = None
    period: str | None = None
    validation_status: ValidationStatus = ValidationStatus.UNSUPPORTED
    validation_reasons: list[str] = []
    confidence: float = 0.0


class ReportSection(BaseModel):
    heading: str
    paragraphs: list[str] = []
    fact_ids: list[str] = []
    chart_spec: dict | None = None


class GeneratedReport(BaseModel):
    report_id: str = ""
    report_type: ReportType = ReportType.PARLIAMENTARY_REPLY
    status: ReportStatus = ReportStatus.QUEUED
    title: str = ""
    sections: list[ReportSection] = []
    claims: list[Claim] = []
    version: int = 1
    parent_id: str | None = None
    created_at: datetime | None = None


class ReviewDecision(BaseModel):
    action: ReviewAction
    claim_id: str | None = None
    reviewer_note: str = ""
    edited_text: str | None = None


class ReportSpec(BaseModel):
    question: str = ""
    report_type: ReportType = ReportType.PARLIAMENTARY_REPLY
    custom_sections: list[str] | None = None
    doc_ids: list[str] = []
    title: str = ""


class ReportJobStatus(BaseModel):
    job_id: str
    status: ReportStatus
    step_index: int = 0
    step_label: str = ""
    progress: int = 0
    error: str | None = None
    result: dict | None = None
    created_at: float | None = None
    updated_at: float | None = None
