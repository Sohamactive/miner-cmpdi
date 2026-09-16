"""PostgreSQL schema for normalized evidence and preserved Docling artifacts."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"
    document_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    filename: Mapped[str] = mapped_column(String(512))
    source_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="indexed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RawDoclingDocument(Base):
    __tablename__ = "raw_docling_documents"
    raw_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.document_id"), index=True)
    batch: Mapped[str | None] = mapped_column(String(32))
    page_range: Mapped[str | None] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSONB)


class Page(Base):
    __tablename__ = "pages"
    page_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.document_id"), index=True)
    page_range: Mapped[str] = mapped_column(String(64))
    batch: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(64), default="processed")


class ChunkRecord(Base):
    __tablename__ = "chunks"
    chunk_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.document_id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    filename: Mapped[str] = mapped_column(String(512))
    page_range: Mapped[str | None] = mapped_column(String(64), index=True)
    batch: Mapped[str | None] = mapped_column(String(32))
    section: Mapped[str | None] = mapped_column(Text)


class Fact(Base):
    __tablename__ = "facts"
    fact_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.document_id"), index=True)
    entity: Mapped[str | None] = mapped_column(String(512), index=True)
    metric: Mapped[str | None] = mapped_column(String(512), index=True)
    period: Mapped[str | None] = mapped_column(String(64), index=True)
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(128))
    page_range: Mapped[str | None] = mapped_column(String(64))
    evidence: Mapped[str] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("document_id", "entity", "metric", "period", "evidence"),)


# --- Report generation tables ---


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(64), default="queued")
    title: Mapped[str] = mapped_column(String(512), default="")
    parameters_json: Mapped[str | None] = mapped_column(Text)
    sections_json: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    parent_id: Mapped[int | None] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ClaimRecord(Base):
    __tablename__ = "claims"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), index=True)
    claim_text: Mapped[str] = mapped_column(Text)
    fact_id: Mapped[int | None] = mapped_column(Integer)
    document_id: Mapped[str | None] = mapped_column(String(64))
    page_range: Mapped[str | None] = mapped_column(String(64))
    evidence_text: Mapped[str] = mapped_column(Text, default="")
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(128))
    validation_status: Mapped[str] = mapped_column(String(32), default="UNSUPPORTED")
    validation_reasons: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReviewDecision(Base):
    __tablename__ = "review_decisions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), index=True)
    claim_id: Mapped[int | None] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(32))
    reviewer_note: Mapped[str] = mapped_column(Text, default="")
    edited_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReportJob(Base):
    __tablename__ = "report_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    report_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(64), default="queued")
    step_index: Mapped[int] = mapped_column(Integer, default=0)
    step_label: Mapped[str] = mapped_column(String(128), default="")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    result_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())