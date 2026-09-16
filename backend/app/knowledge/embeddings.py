"""Embedding providers used by the semantic index."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Iterable


class EmbeddingProvider:
    dimension: int

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        raise NotImplementedError


class FastEmbedProvider(EmbeddingProvider):
    """Local FastEmbed provider; the model is downloaded on first use."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        self.dimension = 384
        self._model = None

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        if self._model is None:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name=self.model_name)
        return [list(vector) for vector in self._model.embed(list(texts))]


class HashEmbeddingProvider(EmbeddingProvider):
    """Dependency-free deterministic provider for unit tests and dry runs."""

    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = [0.0] * self.dimension
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode()).digest()
                index = int.from_bytes(digest[:4], "big") % self.dimension
                vector[index] += 1.0
            norm = sum(value * value for value in vector) ** 0.5 or 1.0
            vectors.append([value / norm for value in vector])
        return vectors