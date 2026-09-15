"""Split PDF into 3-page batches keyed by sha256. No Docling here."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pymupdf

from .config import BATCH_PAGES


def sha256_of(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def split_pdf(
    src: str | Path, out_dir: str | Path, batch_pages: int = BATCH_PAGES
) -> list[dict]:
    """Returns [{i, pages:'1-3', path}] ordered. Creates out_dir."""


    src, out_dir = Path(src), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(src)
    total = len(doc)
    batches: list[dict] = []
    for i, start in enumerate(range(0, total, batch_pages)):
        end = min(start + batch_pages - 1, total - 1)  # 0-based
        b = pymupdf.open()
        b.insert_pdf(doc, from_page=start, to_page=end)
        p = out_dir / f"batch_{i:03d}.pdf"
        b.save(p)
        b.close()
        batches.append({"i": i, "pages": f"{start+1}-{end+1}", "path": str(p)})
    doc.close()
    return batches
