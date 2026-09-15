"""Merge PDF batch artifacts into one ordered output bundle.

What this file does:
1. validate expected batch artifacts
2. merge markdown in batch order
3. merge batch json/stats into one manifest
4. write merged.md + merged_manifest.json

Honest limitation:
- exact <!-- page:N --> insertion inside text is not possible from flattened
  batch markdown alone; that needs page-wise artifacts from the runner.
"""

from __future__ import annotations

import json
from pathlib import Path


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def batch_markdown_path(batch_dir: str | Path, batch_index: int) -> Path:
    batch_dir = Path(batch_dir)
    return batch_dir / f"batch_{batch_index:03d}.md"


def batch_json_path(batch_dir: str | Path, batch_index: int) -> Path:
    batch_dir = Path(batch_dir)
    return batch_dir / f"batch_{batch_index:03d}.json"


def batch_stats_path(batch_dir: str | Path, batch_index: int) -> Path:
    batch_dir = Path(batch_dir)
    return batch_dir / f"batch_{batch_index:03d}.stats.json"


def _page_range(pages: str) -> tuple[int, int]:
    start, end = pages.split("-")
    return int(start), int(end)


def validate_batch_artifacts(
    batch_dir: str | Path,
    batches: list[dict],
) -> dict:
    """Check which expected artifacts exist per batch."""
    batch_dir = Path(batch_dir)

    found = []
    missing = []

    for batch in sorted(batches, key=lambda item: item["i"]):
        md_path = batch_markdown_path(batch_dir, batch["i"])
        json_path = batch_json_path(batch_dir, batch["i"])
        stats_path = batch_stats_path(batch_dir, batch["i"])

        record = {
            "i": batch["i"],
            "pages": batch["pages"],
            "md_exists": md_path.exists(),
            "json_exists": json_path.exists(),
            "stats_exists": stats_path.exists(),
            "md_path": str(md_path),
            "json_path": str(json_path),
            "stats_path": str(stats_path),
        }

        found.append(record)

        if not (record["md_exists"] and record["json_exists"] and record["stats_exists"]):
            missing.append(record)

    return {
        "total_batches": len(batches),
        "found": found,
        "missing": missing,
        "all_present": len(missing) == 0,
    }


def merge_batch_markdown(
    batch_dir: str | Path,
    batches: list[dict],
    output_path: str | Path | None = None,
) -> Path:
    """Merge markdown files in batch order.

    Adds batch markers and page-range markers.
    This is not yet exact per-page insertion.
    """
    batch_dir = Path(batch_dir)
    if output_path is None:
        output_path = batch_dir / "merged.md"
    else:
        output_path = Path(output_path)

    parts: list[str] = []

    for batch in sorted(batches, key=lambda item: item["i"]):
        md_path = batch_markdown_path(batch_dir, batch["i"])
        if not md_path.exists():
            continue

        markdown = md_path.read_text(encoding="utf-8").strip()
        if not markdown:
            continue

        start_page, end_page = _page_range(batch["pages"])

        parts.append(f"\n<!-- batch:{batch['i']:03d} pages:{batch['pages']} -->\n")
        parts.append(f"<!-- page-range:{start_page}-{end_page} -->\n")
        parts.append(markdown)
        parts.append("\n")

    output_path.write_text("".join(parts).strip() + "\n", encoding="utf-8")
    return output_path


def build_merged_manifest(
    batch_dir: str | Path,
    batches: list[dict],
    output_path: str | Path | None = None,
) -> Path:
    """Merge stats/json metadata into one manifest for inspection/debugging."""
    batch_dir = Path(batch_dir)
    if output_path is None:
        output_path = batch_dir / "merged_manifest.json"
    else:
        output_path = Path(output_path)

    merged_batches = []
    total_chars = 0
    total_tables = 0

    for batch in sorted(batches, key=lambda item: item["i"]):
        stats = _read_json(batch_stats_path(batch_dir, batch["i"])) or {}
        doc_json = _read_json(batch_json_path(batch_dir, batch["i"])) or {}

        batch_record = {
            "i": batch["i"],
            "pages": batch["pages"],
            "stats": stats,
            "doc_keys": sorted(doc_json.keys()),
            "tables_count": len(doc_json.get("tables", []))
            if isinstance(doc_json.get("tables", []), list)
            else 0,
        }
        merged_batches.append(batch_record)

        total_chars += int(stats.get("chars", 0))
        total_tables += int(stats.get("tables", 0))

    payload = {
        "summary": {
            "total_batches": len(batches),
            "chars": total_chars,
            "tables": total_tables,
        },
        "batches": merged_batches,
    }

    _write_json(output_path, payload)
    return output_path


def merge_pdf_batch_outputs(
    batch_dir: str | Path,
    batches: list[dict],
) -> dict:
    """Top-level helper: validate + merge markdown + merge manifest."""
    validation = validate_batch_artifacts(batch_dir, batches)
    merged_md = merge_batch_markdown(batch_dir, batches)
    merged_manifest = build_merged_manifest(batch_dir, batches)

    result = {
        "validation": validation,
        "outputs": {
            "merged_md": str(merged_md),
            "merged_manifest": str(merged_manifest),
        },
    }

    _write_json(Path(batch_dir) / "merge_result.json", result)
    return result