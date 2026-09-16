"""Embedding providers used by the semantic index."""

from __future__ import annotations

import hashlib
import os
import threading
from collections.abc import Iterable


_FASTEMBED_MODEL_LOCK = threading.Lock()
_FASTEMBED_MODEL_CACHE: dict[str, object] = {}


class EmbeddingProvider:
    dimension: int

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        raise NotImplementedError


class FastEmbedProvider(EmbeddingProvider):
    """Local FastEmbed provider; the model is downloaded on first use."""

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        self.dimension = 384
        # Model init is expensive. Keep per-process shared cache keyed by model_name.
        self._model = None

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        model = self._model
        if model is None:
            with _FASTEMBED_MODEL_LOCK:
                cached = _FASTEMBED_MODEL_CACHE.get(self.model_name)
                if cached is None:
                    from fastembed import TextEmbedding
                    cached = TextEmbedding(model_name=self.model_name)
                    _FASTEMBED_MODEL_CACHE[self.model_name] = cached
                self._model = cached
                model = cached
        return [list(vector) for vector in model.embed(list(texts))]


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
