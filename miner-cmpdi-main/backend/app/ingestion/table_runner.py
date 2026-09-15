"""Spreadsheet Ingestion Runner (XLSX, XLS, CSV).

Extracts tabular data into clean Markdown tables, JSON AST, and standardized
result.json checkpoint compatible with downstream extraction and QA.
"""

from __future__ import annotations

import csv
import io
import json
import shutil
import time
from pathlib import Path

import openpyxl

from .pdf_splitter import sha256_of


def _format_markdown_table(rows: list[list[object]]) -> str:
    """Format a 2D list into a GitHub Flavored Markdown table."""
    if not rows:
        return ""

    # Normalize row lengths
    max_cols = max(len(r) for r in rows)
    norm_rows = []
    for r in rows:
        norm = [str(c if c is not None else "").replace("\n", " ").strip() for c in r]
        norm += [""] * (max_cols - len(norm))
        norm_rows.append(norm)

    if not norm_rows:
        return ""

    header = norm_rows[0]
    # If header contains only empty strings, create default col headers
    if not any(header):
        header = [f"Column_{j + 1}" for j in range(max_cols)]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]

    for row in norm_rows[1:]:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def run_table(
    file_path: str | Path,
    preset: str = "spreadsheet",
    device: str = "cpu",
    verbose: bool = False,
    resume: bool = True,
) -> dict:
    """Process a spreadsheet (.xlsx, .xls, .csv) and generate standard artifacts."""
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    t0 = time.perf_counter()
    sha = sha256_of(file_path)
    ext = file_path.suffix.lower()

    uploads_dir = Path("data") / "uploads"
    batch_dir = Path("data") / "batches" / sha
    uploads_dir.mkdir(parents=True, exist_ok=True)
    batch_dir.mkdir(parents=True, exist_ok=True)

    stored_file = uploads_dir / f"{sha}{ext}"
    if not stored_file.exists():
        shutil.copy2(file_path, stored_file)

    original_file = batch_dir / f"original{ext}"
    if not original_file.exists():
        shutil.copy2(file_path, original_file)

    sheets_data: list[dict] = []
    markdown_parts: list[str] = [f"# Document: {file_path.name}\n"]

    if ext == ".csv":
        text = file_path.read_text(encoding="utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if rows:
            md_table = _format_markdown_table(rows)
            markdown_parts.append("## Table: Data\n")
            markdown_parts.append(md_table)
            markdown_parts.append("\n")
            sheets_data.append({"sheet_name": "Data", "rows": rows, "cols": len(rows[0]) if rows else 0})
    else:  # .xlsx, .xls
        wb = openpyxl.load_workbook(file_path, data_only=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            rows = []
            for row in ws.iter_rows(values_only=True):
                if any(cell is not None for cell in row):
                    rows.append(list(row))
            if rows:
                md_table = _format_markdown_table(rows)
                markdown_parts.append(f"## Sheet: {sheet_name}\n")
                markdown_parts.append(md_table)
                markdown_parts.append("\n")
                sheets_data.append({"sheet_name": sheet_name, "rows": rows, "cols": len(rows[0]) if rows else 0})

    merged_markdown = "\n".join(markdown_parts)
    total_chars = len(merged_markdown)
    total_tables = len(sheets_data)
    elapsed_secs = round(time.perf_counter() - t0, 2)

    # Standard batch artifacts for single-batch spreadsheet
    batch_stem = "batch_000"
    batch_md_path = batch_dir / f"{batch_stem}.md"
    batch_json_path = batch_dir / f"{batch_stem}.json"
    batch_stats_path = batch_dir / f"{batch_stem}.stats.json"

    batch_md_path.write_text(merged_markdown, encoding="utf-8")

    doc_dict = {
        "schema_name": "SpreadsheetDocument",
        "filename": file_path.name,
        "format": ext.removeprefix("."),
        "tables": sheets_data,
        "total_sheets": len(sheets_data),
    }
    batch_json_path.write_text(json.dumps(doc_dict, indent=2), encoding="utf-8")

    stats = {
        "i": 0,
        "pages": f"1-{len(sheets_data) or 1}",
        "path": str(original_file),
        "preset_used": "spreadsheet_reader",
        "status": "success",
        "seconds": elapsed_secs,
        "chars": total_chars,
        "tables": total_tables,
        "ram_delta_mb": 0.0,
        "error": None,
        "cached": False,
    }
    batch_stats_path.write_text(json.dumps(stats, indent=2), encoding="utf-8")

    # Final merged outputs
    merged_md_path = batch_dir / "merged.md"
    merged_md_path.write_text(merged_markdown, encoding="utf-8")

    manifest = {
        "summary": {
            "total_batches": 1,
            "chars": total_chars,
            "tables": total_tables,
        },
        "batches": [
            {
                "i": 0,
                "pages": stats["pages"],
                "stats": stats,
                "doc_keys": list(doc_dict.keys()),
                "tables_count": total_tables,
            }
        ],
    }
    (batch_dir / "merged_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    result = {
        "document": {
            "doc_id": sha,
            "filename": file_path.name,
            "source_path": str(file_path),
            "stored_pdf": str(stored_file),
            "working_pdf": str(original_file),
            "sha256": sha,
            "preset_requested": preset,
            "device_requested": device,
            "device_resolved": "cpu",
            "total_pages": len(sheets_data) or 1,
            "batch_size": 1,
            "total_batches": 1,
        },
        "batches": [stats],
        "totals": {
            "batches_ok": 1,
            "batches_failed": 0,
            "pages_ok": len(sheets_data) or 1,
            "pages_failed": 0,
            "chars": total_chars,
            "tables": total_tables,
            "seconds_total": elapsed_secs,
        },
        "outputs": {
            "batch_dir": str(batch_dir),
            "merged_md": str(merged_md_path),
            "merged_manifest": str(batch_dir / "merged_manifest.json"),
            "merge_result": None,
            "result_json": str(batch_dir / "result.json"),
            "run_log": str(batch_dir / "run.log"),
        },
    }

    (batch_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
