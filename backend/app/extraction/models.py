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