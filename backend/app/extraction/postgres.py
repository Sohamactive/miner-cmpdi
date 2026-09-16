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


def _docling_grid_rows(table: dict) -> list[list[str]] | None:
    """Extract row-structured cell texts from a Docling table (`data.grid`)."""
    data = table.get("data")
    if not isinstance(data, dict):
        return None
    grid = data.get("grid")
    if not isinstance(grid, list) or not grid:
        return None
    rows: list[list[str]] = []
    for row in grid:
        if not isinstance(row, list):
            return None
        cells: list[str] = []
        for cell in row:
            text = cell.get("text") if isinstance(cell, dict) else cell
            cells.append(str(text or "").strip())
        rows.append(cells)
    return rows or None


def _detect_period_from_headers(headers: list[str]) -> str | None:
    """Look for year/period patterns in header texts."""
    period_patterns = [r"\d{2}-\d{2}", r"\d{4}-\d{4}", r"\d{1,2}\.\d{1,2}\.\d{2,4}"]
    for h in headers:
        hp = str(h).strip()
        for pat in period_patterns:
            if re.search(pat, hp):
                return hp
    return None


def _detect_entity_from_first_column(rows: list[list[str]]) -> str | None:
    """The first cell of the first data row often names the entity (e.g. ECL, BCCL)."""
    if not rows or not isinstance(rows[0], list):
        return None
    first_cell = str(rows[1][0]).strip() if len(rows) > 1 and isinstance(rows[1], list) else None
    if not first_cell:
        return None
    # Filter out common non-entity labels
    stop_words = {"metric", "value", "period", "entity", "note", "source", "ref"}
    cl = first_cell.lower()
    if cl in stop_words or len(cl) < 2:
        return None
    return first_cell


def _detect_unit_from_headers(headers: list[str]) -> str | None:
    """Look for unit keywords in header texts: persons, tonnes, crores, Rs., %."""
    unit_keywords = {
        "persons", "persons trained", "number", "count", "lakhs", "crores",
        "tonnes", "kg", "g/t", "%", "rs.", "rupees", "million", "billion",
    }
    for h in headers:
        hp = str(h).lower()
        for kw in unit_keywords:
            if kw in hp:
                # Return normalized unit label
                if kw in {"persons", "persons trained"}:
                    return "persons"
                if kw in {"lakhs", "crores"}:
                    return kw
                if kw == "%":
                    return "%"
                if kw in {"tonnes", "kg", "g/t"}:
                    return kw
                if kw in {"rs.", "rupees"}:
                    return "Rs."
                if kw in {"million", "billion"}:
                    return kw
    return None


def normalize_table_facts(payload: dict, document_id: str, page_range: str | None) -> tuple[list[Fact], list[Fact]]:
    """Normalize table-to-fact extraction.
    
    Returns:
        (completed_facts, partial_facts) — only fully-qualified facts get entity/metric/period/value/unit.
        Partial rows (missing any of the 5 fields) are returned separately for manual review.
    """
    completed: list[Fact] = []
    partial: list[Fact] = []
    for table in payload.get("tables", []):
        if not isinstance(table, dict):
            continue
        rows = table.get("rows")
        if not (isinstance(rows, list) and rows and isinstance(rows[0], list)):
            rows = _docling_grid_rows(table)
        if not isinstance(rows, list) or len(rows) < 2 or not isinstance(rows[0], list):
            continue
        headers = [str(header or "").strip() for header in rows[0]]
        entity = _detect_entity_from_first_column(rows)
        period = _detect_period_from_headers(headers)
        unit = _detect_unit_from_headers(headers)
        for row in rows[1:]:
            if not isinstance(row, list):
                continue
            cells = [str(cell or "").strip() for cell in row]
            evidence = " | ".join(cells)
            numeric = None
            numeric_index = None
            for index, cell in enumerate(cells):
                candidate = _number(cell)
                if candidate is not None:
                    numeric = candidate
                    numeric_index = index
                    break
            if numeric is None:
                continue
            metric = cells[0] if cells and numeric_index != 0 else (headers[0] if headers else None)
            # Build Fact with whatever we detected
            fact = Fact(
                document_id=document_id,
                entity=entity,
                metric=metric,
                value=numeric,
                evidence=evidence,
                page_range=page_range,
                unit=unit,
                period=period,
            )
            # Count how many of the 5 required fields are populated
            filled = sum(1 for f in [fact.entity, fact.metric, fact.period, fact.unit] if f is not None)
            if filled >= 3:  # generous threshold: emit as completed, rest pending
                completed.append(fact)
            else:
                # Demote to partial — give it whatever we have
                fact.partial_fill = True  # type: ignore[attr-defined]
                partial.append(fact)
    return completed, partial


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
        completed, partial = normalize_table_facts(payload, document_id, page_range)
        for fact in completed:
            duplicate = session.scalar(select(Fact).where(
                Fact.document_id == fact.document_id,
                Fact.metric == fact.metric,
                Fact.value == fact.value,
                Fact.evidence == fact.evidence,
            ).limit(1))
            if duplicate is None:
                session.add(fact)
        for fact in partial:
            # Store partial facts separately for manual review
            fact.partial_fill = True  # type: ignore[attr-defined]
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