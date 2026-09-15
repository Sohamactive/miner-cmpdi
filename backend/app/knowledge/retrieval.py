"""Inspectable semantic retrieval result contract."""

from __future__ import annotations

from dataclasses import dataclass

from .embeddings import EmbeddingProvider
from .qdrant_store import QdrantStore


@dataclass(frozen=True)
class SemanticResult:
    score: float
    text: str
    document_id: str
    filename: str
    page_range: str | None
    batch: str | None
    section: str | None


class SemanticRetriever:
    def __init__(self, store: QdrantStore, embedder: EmbeddingProvider) -> None:
        self.store = store
        self.embedder = embedder

    def search(self, query: str, limit: int = 5, document_id: str | None = None) -> list[SemanticResult]:
        points = self.store.search(self.embedder.embed([query])[0], limit, document_id)
        return [SemanticResult(float(point.score), str((point.payload or {}).get("text", "")),
                               str((point.payload or {}).get("document_id", "")),
                               str((point.payload or {}).get("filename", "")),
                               (point.payload or {}).get("page_range"),
                               (point.payload or {}).get("batch"),
                               (point.payload or {}).get("section")) for point in points]