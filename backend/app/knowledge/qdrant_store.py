"""Qdrant semantic storage; PostgreSQL remains the source of truth."""

from __future__ import annotations

import os
from collections.abc import Sequence

from qdrant_client import QdrantClient, models

from .chunking import Chunk


class QdrantStore:
    def __init__(self, client: QdrantClient | None = None, *, url: str | None = None,
                 collection: str | None = None) -> None:
        self.client = client or QdrantClient(url=url or os.getenv("QDRANT_URL", "http://localhost:6333"))
        self.collection = collection or os.getenv("QDRANT_COLLECTION", "miner_chunks")

    def ensure_collection(self, dimension: int) -> None:
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(size=dimension, distance=models.Distance.COSINE),
            )

    def upsert_chunks(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Each chunk must have exactly one embedding")
        if not chunks:
            return
        self.ensure_collection(len(vectors[0]))
        points = [models.PointStruct(id=chunk.chunk_id, vector=list(vector), payload={
            "chunk_id": chunk.chunk_id, "document_id": chunk.document_id,
            "filename": chunk.filename, "page_range": chunk.page_range,
            "batch": chunk.batch, "section": chunk.section, "text": chunk.text,
        }) for chunk, vector in zip(chunks, vectors, strict=True)]
        self.client.upsert(collection_name=self.collection, points=points)

    def search(self, vector: Sequence[float], limit: int = 5, document_id: str | None = None):
        query_filter = None
        if document_id:
            query_filter = models.Filter(must=[models.FieldCondition(
                key="document_id", match=models.MatchValue(value=document_id)
            )])
        return self.client.query_points(collection_name=self.collection, query=list(vector),
                                        query_filter=query_filter, limit=limit, with_payload=True).points