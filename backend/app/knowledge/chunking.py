"""Provenance-preserving Markdown chunking for ingestion artifacts."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


_BATCH_MARKER = re.compile(r"<!--\s*batch:(?P<batch>\S+)\s+pages:(?P<pages>[^>]+)-->")
_PAGE_MARKER = re.compile(r"<!--\s*page-range:(?P<pages>[^>]+)-->")
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str
    document_id: str
    filename: str
    page_range: str | None
    batch: str | None
    section: str | None


def _chunk_id(document_id: str, ordinal: int, text: str) -> str:
    digest = hashlib.sha256(f"{document_id}:{ordinal}:{text}".encode()).hexdigest()
    return digest[:32]


def chunk_markdown(
    markdown: str,
    *,
    document_id: str,
    filename: str,
    max_chars: int = 1800,
    min_chars: int = 80,
) -> list[Chunk]:
    """Split Markdown by sections/paragraphs while carrying source markers."""
    chunks: list[Chunk] = []
    section: str | None = None
    batch: str | None = None
    page_range: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        text = "\n".join(buffer).strip()
        if text and len(text) >= min_chars:
            ordinal = len(chunks)
            chunks.append(Chunk(_chunk_id(document_id, ordinal, text), text, document_id,
                                filename, page_range, batch, section))
        buffer = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        batch_match = _BATCH_MARKER.search(line)
        page_match = _PAGE_MARKER.search(line)
        if batch_match:
            flush()
            batch = batch_match.group("batch")
            page_range = batch_match.group("pages").strip()
            continue
        if page_match:
            page_range = page_match.group("pages").strip()
            continue
        heading = _HEADING.match(line)
        if heading:
            flush()
            section = heading.group(2)
            buffer.append(line)
            continue
        if not line:
            if sum(len(part) + 1 for part in buffer) >= min_chars:
                flush()
            continue
        buffer.append(line)
        if sum(len(part) + 1 for part in buffer) >= max_chars:
            flush()
    flush()
    return chunks