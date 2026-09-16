"""Bridge existing ingestion artifacts into PostgreSQL and Qdrant."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from app.extraction.postgres import create_session, persist_artifacts

from .chunking import chunk_markdown
from .embeddings import EmbeddingProvider
from .qdrant_store import QdrantStore


_FAILED_STATUSES = {"failed", "failed_all_fallbacks", "timeout"}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def index_ingestion_artifacts(
    batch_dir: str | Path,
    *,
    embedder: EmbeddingProvider,
    qdrant: QdrantStore,
    database_url: str | None = None,
    embed_batch_size: int | None = None,
) -> dict[str, int | str]:
    """Index only successful batch artifacts produced by existing ingestion."""
    batch_path = Path(batch_dir)
    result = _read_json(batch_path / "result.json")
    document = result["document"]
    document_id = str(document["doc_id"])
    merged_path = Path(result["outputs"]["merged_md"])
    markdown = merged_path.read_text(encoding="utf-8")
    chunks = chunk_markdown(markdown, document_id=document_id, filename=document["filename"])

    raw_payloads: list[tuple[dict[str, Any], str | None, str | None]] = []
    indexed_batches = 0
    for batch in result.get("batches", []):
        if str(batch.get("status", "")).lower() in _FAILED_STATUSES:
            continue
        json_path = batch_path / f"batch_{int(batch['i']):03d}.json"
        if json_path.exists():
            raw_payloads.append((
                _read_json(json_path),
                str(batch.get("i")) if batch.get("i") is not None else None,
                str(batch.get("pages")) if batch.get("pages") else None,
            ))
            indexed_batches += 1

    session = create_session(database_url)
    try:
        persist_artifacts(session, document_id=document_id, filename=document["filename"],
                          source_path=document.get("source_path"), chunks=chunks,
                          raw_payloads=raw_payloads)
    finally:
        session.close()

    # Qdrant is rebuildable mirror. Upsert in small embed batches to avoid OOM.
    if embed_batch_size is None:
        embed_batch_size = int(os.getenv("EMBED_BATCH_SIZE", "16"))
    if embed_batch_size <= 0:
        embed_batch_size = 16

    if chunks:
        qdrant.ensure_collection(embedder.dimension)
        for start in range(0, len(chunks), embed_batch_size):
            batch = chunks[start : start + embed_batch_size]
            vectors = embedder.embed([c.text for c in batch])
            qdrant.upsert_chunks(batch, vectors)
    return {"document_id": document_id, "chunks": len(chunks), "batches": indexed_batches}
