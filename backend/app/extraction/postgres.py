"""Database access and conservative Docling table normalization."""

from __future__ import annotations

import json
import os
import re
import hashlib
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.knowledge.chunking import Chunk
from .models import Base, ChunkRecord, Document, Fact, RawDoclingDocument


def database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql+psycopg://localhost:5432/miner_db")


def create_session(url: str | None = None) -> Session:
    return Session(create_engine(url or database_url(), pool_pre_ping=True))


def create_schema(session: Session) -> None:
    Base.metadata.create_all(session.get_bind())


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"-?\d[\d,]*(?:\.\d+)?", value)
        if match:
            return float(match.group().replace(",", ""))
    return None


def normalize_table_facts(payload: dict, document_id: str, page_range: str | None) -> list[Fact]:
    """Normalize only tables with a clear header/value shape; preserve evidence."""
    facts: list[Fact] = []
    for table in payload.get("tables", []):
        rows = table.get("rows") if isinstance(table, dict) else None
        if not isinstance(rows, list) or len(rows) < 2 or not isinstance(rows[0], list):
            continue
        headers = [str(header or "").strip() for header in rows[0]]
        for row in rows[1:]:
            if not isinstance(row, list):
                continue
            cells = [str(cell or "").strip() for cell in row]
            evidence = " | ".join(cells)
            for index, value in enumerate(cells):
                numeric = _number(value)
                if numeric is None or index >= len(headers):
                    continue
                facts.append(Fact(document_id=document_id, metric=headers[index] or None,
                                  value=numeric, evidence=evidence, page_range=page_range))
    return facts


def persist_artifacts(session: Session, *, document_id: str, filename: str,
                      chunks: list[Chunk],
                      raw_payloads: list[tuple[dict, str | None, str | None]] | None = None,
                      source_path: str | None = None) -> None:
    create_schema(session)
    if session.get(Document, document_id) is None:
        session.add(Document(document_id=document_id, filename=filename, source_path=source_path))
    for chunk in chunks:
        if session.get(ChunkRecord, chunk.chunk_id) is None:
            session.add(ChunkRecord(**chunk.__dict__))
    for payload, batch, page_range in raw_payloads or []:
        raw_id = hashlib.sha256(json.dumps(
            [document_id, batch, page_range, payload], sort_keys=True
        ).encode()).hexdigest()[:64]
        session.merge(RawDoclingDocument(raw_id=raw_id, document_id=document_id,
                                         batch=batch, page_range=page_range, payload=payload))
        for fact in normalize_table_facts(payload, document_id, page_range):
            duplicate = session.scalar(select(Fact).where(
                Fact.document_id == fact.document_id,
                Fact.metric == fact.metric,
                Fact.value == fact.value,
                Fact.evidence == fact.evidence,
            ).limit(1))
            if duplicate is None:
                session.add(fact)
    session.commit()


def search_facts(session: Session, *, entity: str | None = None, metric: str | None = None,
                 period: str | None = None, limit: int = 20) -> list[Fact]:
    query = select(Fact).limit(limit)
    if entity:
        query = query.where(Fact.entity.ilike(f"%{entity}%"))
    if metric:
        query = query.where(Fact.metric.ilike(f"%{metric}%"))
    if period:
        query = query.where(Fact.period == period)
    return list(session.scalars(query))


def load_docling_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))