"""Modular PDF Ingestion Runner with Parallel Batch Processing & Resiliency.

Structure:
- Section 1: Types & Utilities
- Section 2: Artifact Inspection & Fast Resume Recovery
- Section 3: Subprocess Worker, Fallback Chain & Emergency PyMuPDF Fallback
- Section 4: Thread-Safe Checkpoint Writer & State Builder
- Section 5: Parallel Orchestrator (run_pdf)
"""

from __future__ import annotations

import concurrent.futures
import json
import logging
import multiprocessing as mp
import queue  # stdlib Empty exception, raised by mp.Queue.get(timeout=...)
import re
import shutil
import threading
import time
import traceback
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

import pymupdf

from .config import (
    BATCH_PAGES,
    DIGITAL_TEXT_CHAR_THRESHOLD,
    DIGITAL_TEXT_SAMPLE_PAGES,
    LOAD_TIMEOUT_S,
    MAX_WORKERS,
    TIMEOUTS_S,
    resolve_device,
)
from .logging_setup import setup_clean_logs
from .pdf_merge import merge_pdf_batch_outputs
from .pdf_splitter import sha256_of, split_pdf

# =====================================================================
# SECTION 1: Types & Utilities
# =====================================================================


def _page_count(pdf_path: Path) -> int:
    """Return total page count of a PDF."""
    doc = pymupdf.open(pdf_path)
    total = len(doc)
    doc.close()
    return total


def _has_digital_text_layer(
    pdf_path: Path,
    sample_pages: int = DIGITAL_TEXT_SAMPLE_PAGES,
    threshold: float = DIGITAL_TEXT_CHAR_THRESHOLD,
) -> tuple[bool, float, int]:
    """Cheap born-digital check: sample pages via PyMuPDF text extraction.

    Why this exists: OCR-based presets (scanned/light_table/ocr_only) can
    silently return "PARTIAL_SUCCESS with 0 chars" on documents that already
    have a perfectly good text layer, wasting minutes on EasyOCR before the
    PyMuPDF emergency fallback recovers the text. Sampling the native text
    layer up front lets such docs start on the fast digital path instead.

    Returns (is_digital, density, sampled) where density is the average
    non-whitespace chars per sampled page. Unreadable PDFs safely report
    (False, 0.0, 0) so callers fall back to the scanned path.
    """
    try:
        doc = pymupdf.open(pdf_path)
    except Exception:
        return False, 0.0, 0
    try:
        total = len(doc)
        sampled = max(1, min(sample_pages, total)) if total else 0
        if sampled == 0:
            return False, 0.0, 0
        chars = 0
        for i in range(sampled):
            try:
                text = doc[i].get_text("text") or ""
            except Exception:
                text = ""
            chars += sum(1 for ch in text if not ch.isspace())
        density = chars / sampled
        return density >= threshold, density, sampled
    finally:
        doc.close()


def _resolve_starting_preset(
    pdf_path: Path,
    preset: str | None,
    auto_detect: bool,
    sha: str,
    log: logging.Logger,
) -> str:
    """Resolve the effective starting preset for the fallback chain.

    preset=None means the caller did not choose (legacy default "scanned");
    only then, with auto_detect on, a detected text layer upgrades the start
    to "digital". An explicit preset name is always respected as-is so callers
    keep full control; pass auto_detect=False to force the legacy behavior of
    starting exactly where preset (or the default) says.
    """
    requested = preset if preset is not None else "scanned"
    if not auto_detect or preset is not None or requested != "scanned":
        return requested
    is_digital, density, sampled = _has_digital_text_layer(pdf_path)
    log.info(
        "[detect %s] text layer %s: digital density=%.1f chars/page over %d sampled pages -> preset=%s",
        sha[:12],
        "found" if is_digital else "not found",
        density,
        sampled,
        "digital" if is_digital else "scanned",
    )
    return "digital" if is_digital else "scanned"


def _page_span_count(pages: str) -> int:
    """'1-3' -> 3, '10-10' -> 1."""
    start, end = pages.split("-")
    return int(end) - int(start) + 1


def _count_tables(doc_dict: dict | None) -> int:
    """Best-effort table count from Docling export dict."""
    if not isinstance(doc_dict, dict):
        return 0
    tables = doc_dict.get("tables", [])
    return len(tables) if isinstance(tables, list) else 0


def _memory_mb() -> float | None:
    """Return current process RSS memory in MB."""
    if psutil is None:
        return None
    proc = psutil.Process()
    return round(proc.memory_info().rss / (1024 * 1024), 1)


def _write_json(path: Path, payload: dict) -> None:
    """Write JSON with UTF-8 encoding and parent directory creation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict | None:
    """Read JSON file if it exists, returning None otherwise."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _batch_paths(batch_dir: Path, batch_index: int) -> dict[str, Path]:
    """Return expected artifact paths for a given batch index."""
    stem = f"batch_{batch_index:03d}"
    return {
        "md": batch_dir / f"{stem}.md",
        "json": batch_dir / f"{stem}.json",
        "stats": batch_dir / f"{stem}.stats.json",
    }


def _status_slug(status: object) -> str:
    """Normalize status enum / string."""
    return str(status).strip().lower().removeprefix("conversionstatus.")


def _is_completed_status(status: object) -> bool:
    """Determine if status represents a successfully processed or recovered batch."""
    return _status_slug(status) in {
        "success",
        "partial_success",
        "cached",
        "completed_from_artifacts",
        "partial_fallback_pymupdf",
    }


def _has_any_artifact(paths: dict[str, Path]) -> bool:
    """Check if any of the batch artifacts exist on disk."""
    return any(path.exists() for path in paths.values())


# =====================================================================
# SECTION 2: Artifact Inspection & Fast Resume Recovery
# =====================================================================


def _recover_batch_from_artifacts(
    batch: dict,
    paths: dict[str, Path],
) -> tuple[dict | None, str | None]:
    """Recover one completed batch from md/json/stats artifacts if trustworthy."""
    if not all(path.exists() for path in paths.values()):
        return None, "missing_artifacts"

    try:
        markdown = paths["md"].read_text(encoding="utf-8")
        doc_json = _read_json(paths["json"])
        stats = _read_json(paths["stats"])
    except Exception as exc:
        return None, f"artifact_read_error:{exc}"

    if not isinstance(doc_json, dict):
        return None, "invalid_doc_json"
    if not isinstance(stats, dict):
        return None, "invalid_stats_json"
    if stats.get("i") != batch["i"]:
        return None, "stats_index_mismatch"
    if stats.get("pages") != batch["pages"]:
        return None, "stats_pages_mismatch"
    if not _is_completed_status(stats.get("status")):
        return None, f"non_resumable_status:{stats.get('status')}"

    try:
        seconds = float(stats.get("seconds", 0.0))
        chars = int(stats.get("chars", 0))
        tables = int(stats.get("tables", 0))
    except (TypeError, ValueError):
        return None, "invalid_numeric_stats"

    if seconds < 0 or chars < 0 or tables < 0:
        return None, "negative_numeric_stats"
    if chars > 0 and not markdown.strip():
        return None, "markdown_empty_with_positive_chars"

    recovered = dict(stats)
    recovered["status"] = "completed_from_artifacts"
    recovered["cached"] = True
    recovered["error"] = None
    recovered["recovered_from_artifacts"] = True
    return recovered, None


def _scan_and_recover_batches(
    batch_dir: Path,
    batches: list[dict],
    resume: bool,
    log: logging.Logger,
    sha: str,
) -> tuple[dict[int, dict], list[dict]]:
    """Scan all batch artifacts. Returns (recovered_by_i, pending_batches)."""
    recovered_by_i: dict[int, dict] = {}
    pending_batches: list[dict] = []
    needs_rebuild = 0

    if not resume:
        return {}, list(batches)

    for batch in batches:
        paths = _batch_paths(batch_dir, batch["i"])
        recovered, reason = _recover_batch_from_artifacts(batch, paths)
        if recovered is not None:
            recovered_by_i[batch["i"]] = recovered
        else:
            pending_batches.append(batch)
            if _has_any_artifact(paths):
                needs_rebuild += 1
                log.warning(
                    "[resume %s] pp %s artifacts incomplete -> rebuild (%s)",
                    sha[:12],
                    batch["pages"],
                    reason,
                )

    if recovered_by_i:
        log.info(
            "[resume %s] recovered=%d pending=%d rebuild=%d from batch artifacts",
            sha[:12],
            len(recovered_by_i),
            len(pending_batches),
            needs_rebuild,
        )

    return recovered_by_i, pending_batches


# =====================================================================
# SECTION 3: Subprocess Worker, Fallbacks & PyMuPDF Emergency Salvage
# =====================================================================


def _worker_convert(batch: dict, preset: str, device: str, q: mp.Queue) -> None:
    """Run one Docling conversion in a separate process, in two reported phases.

    Phase 1 (load): import torch/docling + build the preset's converter
    (models loaded from disk/HF cache). Sends a "ready" message the instant
    this finishes, so the parent's conversion timeout only starts counting
    AFTER cold-start is done — it no longer eats into TIMEOUTS_S.

    Phase 2 (convert): the actual page conversion. Sends a "result" message
    with the same shape as before.
    """
    t0 = time.perf_counter()

    # ---- Phase 1: load ----
    try:
        from .converter import get_converter
        from .logging_setup import setup_clean_logs

        setup_clean_logs(verbose=False)
        mem_before = _memory_mb()
        converter = get_converter(preset=preset, device=device)
        load_secs = round(time.perf_counter() - t0, 1)
        q.put({"type": "ready", "load_seconds": load_secs})
    except BaseException as exc:
        load_secs = round(time.perf_counter() - t0, 1)
        try:
            q.put(
                {
                    "type": "load_failed",
                    "load_seconds": load_secs,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
        except Exception:
            raise
        return

    # ---- Phase 2: convert (this is the phase timeout_s now actually measures) ----
    t1 = time.perf_counter()
    try:
        result = converter.convert(batch["path"])
        secs = round(time.perf_counter() - t1, 1)

        markdown = result.document.export_to_markdown()
        doc_dict = result.document.export_to_dict()

        mem_after = _memory_mb()
        mem_delta = (
            round(mem_after - mem_before, 1)
            if mem_before is not None and mem_after is not None
            else None
        )

        is_empty = not markdown.strip()
        q.put(
            {
                "type": "result",
                "ok": not is_empty,
                "stats": {
                    "i": batch["i"],
                    "pages": batch["pages"],
                    "path": batch["path"],
                    "preset_used": preset,
                    "status": str(result.status),
                    "seconds": secs,  # conversion-only, load time excluded
                    "load_seconds": load_secs,  # kept visible for diagnostics
                    "chars": len(markdown),
                    "tables": _count_tables(doc_dict),
                    "ram_delta_mb": mem_delta,
                    "error": "PARTIAL_SUCCESS with 0 chars" if is_empty else None,
                    "cached": False,
                },
                "markdown": markdown,
                "doc_dict": doc_dict,
                "error": "PARTIAL_SUCCESS with 0 chars" if is_empty else None,
            }
        )
    except BaseException as exc:
        secs = round(time.perf_counter() - t1, 1)
        mem_after = _memory_mb()
        mem_delta = (
            round(mem_after - mem_before, 1)
            if mem_before is not None and mem_after is not None
            else None
        )
        try:
            q.put(
                {
                    "type": "result",
                    "ok": False,
                    "stats": {
                        "i": batch["i"],
                        "pages": batch["pages"],
                        "path": batch["path"],
                        "preset_used": preset,
                        "status": "failed",
                        "seconds": secs,
                        "load_seconds": load_secs,
                        "chars": 0,
                        "tables": 0,
                        "ram_delta_mb": mem_delta,
                        "error": str(exc),
                        "cached": False,
                    },
                    "markdown": "",
                    "doc_dict": None,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            )
        except Exception:
            raise


def _timeout_stats(batch: dict, preset: str, timeout_s: float, phase: str) -> dict:
    """Shared stats-dict builder for the timeout/failure exit paths below."""
    return {
        "i": batch["i"],
        "pages": batch["pages"],
        "path": batch["path"],
        "preset_used": preset,
        "status": "timeout",
        "seconds": float(timeout_s),
        "chars": 0,
        "tables": 0,
        "ram_delta_mb": None,
        "error": f"hard timeout during {phase} after {timeout_s}s",
        "cached": False,
    }


def _kill_proc(proc: mp.Process) -> None:
    """Terminate, escalate to kill if needed. Shared by both timeout paths."""
    if not proc.is_alive():
        return
    proc.terminate()
    proc.join(10)
    if proc.is_alive():
        try:
            proc.kill()
        except Exception:  # noqa: BLE001, S110
            pass
        proc.join(10)


def _run_one_batch(
    batch: dict,
    preset: str,
    device: str,
    timeout_s: int,
    load_timeout_s: float = LOAD_TIMEOUT_S,
    log: logging.Logger | None = None,
    batch_pos: int | None = None,
    total_batches: int | None = None,
) -> tuple[dict, str, dict | None, str | None]:
    """Launch an isolated subprocess for one preset attempt.

    Two separately-timed phases:
      1. load_timeout_s  — waits for the worker's "ready" signal (import +
         model construction). NOT counted against the conversion budget.
      2. timeout_s        — the existing per-preset budget from TIMEOUTS_S,
         now measuring only actual Docling conversion time.
    """
    ctx = mp.get_context("spawn")
    q: mp.Queue = ctx.Queue()
    proc = ctx.Process(target=_worker_convert, args=(batch, preset, device, q))
    proc.start()

    HEARTBEAT_S = 30
    label = (
        f"{batch_pos:02d}/{total_batches:02d}" if batch_pos and total_batches else "?"
    )

    # ---- Phase 1: wait for model load to finish ----
    load_started = time.perf_counter()
    load_elapsed = 0.0
    ready_msg = None
    while load_elapsed < load_timeout_s:
        remaining = load_timeout_s - load_elapsed
        try:
            ready_msg = q.get(timeout=min(HEARTBEAT_S, remaining))
            break
        except queue.Empty:
            load_elapsed = time.perf_counter() - load_started
            if not proc.is_alive():
                break
            if log is not None:
                log.info(
                    "[batch %s] pp %s preset=%s loading models ... %.0fs/%.0fs",
                    label,
                    batch["pages"],
                    preset,
                    load_elapsed,
                    load_timeout_s,
                )

    if ready_msg is None:
        # Either load_timeout_s expired, or the process died mid-load.
        _kill_proc(proc)
        try:
            q.close()
        except Exception:  # noqa: BLE001, S110
            pass
        stats = _timeout_stats(batch, preset, load_timeout_s, "model load")
        return stats, "", None, stats["error"]

    if ready_msg.get("type") == "load_failed":
        _kill_proc(proc)
        err = ready_msg.get("error", "model load failed")
        trace = ready_msg.get("traceback")
        if trace:
            err = f"{err}\n{trace}"
        stats = {
            "i": batch["i"],
            "pages": batch["pages"],
            "path": batch["path"],
            "preset_used": preset,
            "status": "failed",
            "seconds": ready_msg.get("load_seconds", 0.0),
            "chars": 0,
            "tables": 0,
            "ram_delta_mb": None,
            "error": err,
            "cached": False,
        }
        return stats, "", None, err

    # ---- Phase 2: wait for the actual conversion result ----
    convert_started = time.perf_counter()
    convert_elapsed = 0.0
    payload = None
    while convert_elapsed < timeout_s:
        remaining = timeout_s - convert_elapsed
        try:
            payload = q.get(timeout=min(HEARTBEAT_S, remaining))
            break
        except queue.Empty:
            convert_elapsed = time.perf_counter() - convert_started
            if not proc.is_alive():
                break
            if log is not None:
                log.info(
                    "[batch %s] pp %s preset=%s still converting after %.0fs/%.0fs ...",
                    label,
                    batch["pages"],
                    preset,
                    convert_elapsed,
                    timeout_s,
                )

    if payload is None:
        _kill_proc(proc)
        try:
            q.close()
        except Exception:  # noqa: BLE001, S110
            pass
        stats = _timeout_stats(batch, preset, timeout_s, "conversion")
        return stats, "", None, stats["error"]

    proc.join(5)  # let it exit naturally; it's already sent its final message

    err = payload.get("error") if not payload.get("ok") else None
    trace = payload.get("traceback")
    if trace:
        err = f"{err}\n{trace}"
    return payload["stats"], payload["markdown"], payload["doc_dict"], err


def _looks_tabular(text: str, min_hits: int = 2) -> bool:
    """Heuristic: page text with aligned numeric columns find_tables() may miss.

    Counts lines that combine 2+ column gaps (2+ spaces or a tab) with digit
    content; min_hits such lines suggests tabular data flattened to text.
    """
    hits = 0
    for line in text.splitlines():
        if len(re.findall(r" {2,}|\t", line)) >= 2 and any(ch.isdigit() for ch in line):
            hits += 1
            if hits >= min_hits:
                return True
    return False


def _emergency_pymupdf_fallback(
    batch: dict,
    log: logging.Logger | None = None,
) -> tuple[dict, str, dict]:
    """Native C extraction fallback using PyMuPDF when Docling crashes or hangs.

    Guarantees no lost pages or zero-text blindspots on corrupted/heavy scan pages.
    """
    t0 = time.perf_counter()
    pdf_path = Path(batch["path"])
    doc = pymupdf.open(pdf_path)

    pages_span = batch["pages"]
    try:
        span_start = int(str(pages_span).split("-")[0])
    except (ValueError, IndexError):
        span_start = 1

    md_lines: list[str] = [
        f"<!-- fallback: emergency_pymupdf pages:{batch['pages']} -->\n"
    ]
    extracted_tables = []
    total_chars = 0

    for page_idx, page in enumerate(doc):  # type: ignore
        page_num_str = f"Page {page_idx + 1}"
        md_lines.append(f"### {page_num_str}\n")

        # 1. Extract raw text stream
        text = page.get_text("text").strip()
        if text:
            md_lines.append(text)
            md_lines.append("\n")
            total_chars += len(text)

        # 2. Extract tables via PyMuPDF native table finder
        found_tables = 0
        try:
            tabs = page.find_tables()
            for tab in tabs.tables:
                df = tab.extract()
                if df and len(df) > 1:
                    extracted_tables.append({"page": page_idx + 1, "rows": df})
                    found_tables += 1
                    # Format as basic markdown table
                    header = [str(c or "").strip() for c in df[0]]
                    md_lines.append("| " + " | ".join(header) + " |")
                    md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")
                    for row in df[1:]:
                        r_str = [str(c or "").replace("\n", " ").strip() for c in row]
                        md_lines.append("| " + " | ".join(r_str) + " |")
                    md_lines.append("\n")
        except Exception as exc:
            # Visibility only: behavior stays on the flat-text path.
            if log is not None:
                log.warning(
                    "[fallback pp %s] page %d: find_tables() raised %s; "
                    "tabular data (if any) kept as flat text",
                    pages_span,
                    span_start + page_idx,
                    exc,
                )
        if found_tables == 0 and text and _looks_tabular(text):  # noqa: SIM102
            # find_tables() succeeded but saw nothing tabular on a page whose
            # text looks columnar — flag the silent fidelity loss.
            if log is not None:
                log.warning(
                    "[fallback pp %s] page %d: table detection found 0 tables "
                    "(source may contain tabular data lost to flat text)",
                    pages_span,
                    span_start + page_idx,
                )

    doc.close()
    secs = round(time.perf_counter() - t0, 2)
    markdown = "\n".join(md_lines)

    stats = {
        "i": batch["i"],
        "pages": batch["pages"],
        "path": batch["path"],
        "preset_used": "emergency_pymupdf",
        "status": "partial_fallback_pymupdf",
        "seconds": secs,
        "chars": len(markdown),
        "tables": len(extracted_tables),
        "ram_delta_mb": 0.0,
        "error": "Docling presets failed; recovered via PyMuPDF native fallback",
        "cached": False,
    }

    doc_dict = {
        "schema_name": "PyMuPDFFallbackDocument",
        "fallback": True,
        "pages": batch["pages"],
        "tables": extracted_tables,
        "chars": len(markdown),
    }

    return stats, markdown, doc_dict


def _process_batch_with_fallbacks(
    batch: dict,
    preset: str,
    device: str,
    batch_dir: Path,
    log: logging.Logger,
    batch_pos: int,
    total_batches: int,
) -> dict:
    """Execute preset fallback chain for one batch, writing artifacts upon completion."""
    paths = _batch_paths(batch_dir, batch["i"])

    fallback_chain = [preset]
    if preset == "digital":
        fallback_candidates = ("scanned", "light_table", "ocr_only")
    else:
        fallback_candidates = ("light_table", "ocr_only")
    for name in fallback_candidates:
        if name not in fallback_chain:
            fallback_chain.append(name)

    final_stats = None
    final_markdown = ""
    final_doc_dict = None

    for attempt_preset in fallback_chain:
        timeout_s = TIMEOUTS_S.get(attempt_preset, 180)
        log.info(
            "[batch %02d/%02d] START pp %s preset=%s timeout=%ss",
            batch_pos,
            total_batches,
            batch["pages"],
            attempt_preset,
            timeout_s,
        )
        stats, markdown, doc_dict, err = _run_one_batch(
            batch=batch,
            preset=attempt_preset,
            device=device,
            timeout_s=timeout_s,
            log=log,
            batch_pos=batch_pos,
            total_batches=total_batches,
        )

        if err is None and markdown.strip():
            final_stats = stats
            final_markdown = markdown
            final_doc_dict = doc_dict
            break

        if err is None and not markdown.strip():
            # Docling returned a result but produced zero content — treat as
            # failure so we continue the fallback chain.
            err = stats.get("error") or "empty output (0 chars)"
            log.warning(
                "[batch %02d/%02d] pp %s preset=%s returned 0 chars — continuing fallback chain",
                batch_pos,
                total_batches,
                batch["pages"],
                attempt_preset,
            )

        log.error(
            "[batch %02d/%02d] pp %s FAILED with %s after %.1fs: %s",
            batch_pos,
            total_batches,
            batch["pages"],
            attempt_preset,
            stats["seconds"],
            err,
        )

    # If all Docling presets failed, trigger Emergency PyMuPDF Fallback
    if final_stats is None:
        log.warning(
            "[batch %02d/%02d] pp %s all Docling presets failed -> attempting PyMuPDF emergency fallback",
            batch_pos,
            total_batches,
            batch["pages"],
        )
        try:
            final_stats, final_markdown, final_doc_dict = _emergency_pymupdf_fallback(
                batch, log=log
            )
            log.info(
                "[batch %02d/%02d] pp %s recovered via PyMuPDF fallback: %d chars, %d tables",
                batch_pos,
                total_batches,
                batch["pages"],
                final_stats["chars"],
                final_stats["tables"],
            )
        except Exception as exc:
            log.critical(
                "[batch %02d/%02d] pp %s emergency PyMuPDF fallback also failed: %s",
                batch_pos,
                total_batches,
                batch["pages"],
                exc,
            )
            final_stats = {
                "i": batch["i"],
                "pages": batch["pages"],
                "path": batch["path"],
                "preset_used": None,
                "status": "failed_all_fallbacks",
                "seconds": 0.0,
                "chars": 0,
                "tables": 0,
                "ram_delta_mb": None,
                "error": f"all fallbacks failed: {exc}",
                "cached": False,
            }
            final_markdown = ""
            final_doc_dict = None

    # Write artifacts to batch directory
    paths["md"].write_text(final_markdown, encoding="utf-8")
    if final_doc_dict is not None:
        _write_json(paths["json"], final_doc_dict)
    _write_json(paths["stats"], final_stats)

    ram_text = (
        f" | +{final_stats['ram_delta_mb']}MB"
        if final_stats.get("ram_delta_mb") is not None
        else ""
    )

    log.info(
        "[batch %02d/%02d] pp %s .... %s %.1fs | %.1fk chars | %d tables | %s%s",
        batch_pos,
        total_batches,
        batch["pages"],
        final_stats["status"],
        final_stats["seconds"],
        final_stats["chars"] / 1000,
        final_stats["tables"],
        device,
        ram_text,
    )

    return final_stats


# =====================================================================
# SECTION 4: Thread-Safe State & Checkpoint Builder
# =====================================================================


def _build_result(
    *,
    sha: str,
    pdf_path: Path,
    stored_pdf: Path,
    original_pdf: Path,
    preset: str,
    device: str,
    resolved_device: str,
    total_pages: int,
    batches: list[dict],
    batch_results: list[dict],
    total_chars: int,
    total_tables: int,
    seconds_total: float,
    batch_dir: Path,
    result_json_path: Path,
    merged_md_path: Path | None = None,
    merged_manifest_path: Path | None = None,
) -> dict:
    """Build standardized master result record matching future coal.db schema."""
    pages_ok = sum(
        _page_span_count(item["pages"])
        for item in batch_results
        if str(item.get("status", "")).lower() != "failed_all_fallbacks"
    )
    pages_failed = total_pages - pages_ok
    return {
        "document": {
            "doc_id": sha,
            "filename": pdf_path.name,
            "source_path": str(pdf_path),
            "stored_pdf": str(stored_pdf),
            "working_pdf": str(original_pdf),
            "sha256": sha,
            "preset_requested": preset,
            "device_requested": device,
            "device_resolved": resolved_device,
            "total_pages": total_pages,
            "batch_size": BATCH_PAGES,
            "total_batches": len(batches),
        },
        "batches": sorted(batch_results, key=lambda b: b.get("i", 0)),
        "totals": {
            "batches_ok": sum(
                1
                for item in batch_results
                if str(item.get("status", "")).lower() != "failed_all_fallbacks"
            ),
            "batches_failed": sum(
                1
                for item in batch_results
                if str(item.get("status", "")).lower() == "failed_all_fallbacks"
            ),
            "pages_ok": pages_ok,
            "pages_failed": pages_failed,
            "chars": total_chars,
            "tables": total_tables,
            "seconds_total": round(seconds_total, 1),
        },
        "outputs": {
            "batch_dir": str(batch_dir),
            "merged_md": str(merged_md_path) if merged_md_path else None,
            "merged_manifest": (
                str(merged_manifest_path) if merged_manifest_path else None
            ),
            "merge_result": str(batch_dir / "merge_result.json"),
            "result_json": str(result_json_path),
            "run_log": str(batch_dir / "run.log"),
        },
    }


# =====================================================================
# SECTION 5: Parallel Orchestrator (run_pdf)
# =====================================================================


def run_pdf(
    pdf_path: str | Path,
    preset: str | None = None,
    device: str = "auto",
    verbose: bool = False,
    resume: bool = True,
    max_workers: int | None = None,
    auto_detect: bool = True,
) -> dict:
    """Process one PDF with parallel batch execution, auto-resume, and hard timeouts.

    preset=None (default) means "no explicit choice": the legacy "scanned"
    start applies, unless auto_detect upgrades a text-layer PDF to "digital".
    Pass a preset name to force that start, or auto_detect=False to force the
    legacy starting behavior unconditionally.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    sha = sha256_of(pdf_path)
    resolved_device = resolve_device(device)
    total_pages = _page_count(pdf_path)

    uploads_dir = Path("data") / "uploads"
    batch_dir = Path("data") / "batches" / sha
    result_json_path = batch_dir / "result.json"

    uploads_dir.mkdir(parents=True, exist_ok=True)
    batch_dir.mkdir(parents=True, exist_ok=True)

    stored_pdf = uploads_dir / f"{sha}.pdf"
    if not stored_pdf.exists():
        shutil.copy2(pdf_path, stored_pdf)

    original_pdf = batch_dir / "original.pdf"
    if not original_pdf.exists():
        shutil.copy2(pdf_path, original_pdf)

    log = setup_clean_logs(
        verbose=verbose,
        log_file=batch_dir / "run.log",
    )

    # Single choke point for preset selection: upgrade default-path digital
    # docs to the fast text path before any batch work starts.
    preset = _resolve_starting_preset(pdf_path, preset, auto_detect, sha, log)

    batches = split_pdf(original_pdf, batch_dir, batch_pages=BATCH_PAGES)
    # Parallel workers (default MAX_WORKERS=2, override via max_workers arg
    # or INGESTION_MAX_WORKERS env). Heartbeat logs + internal Docling
    # timeouts + terminate/kill in _run_one_batch keep parallel batches
    # from ever looking or staying stuck.
    if max_workers is not None:
        num_workers = max(1, int(max_workers))
    else:
        num_workers = MAX_WORKERS

    log.info(
        "[ingest %s] file=%s total_pages=%d batch_size=%d total_batches=%d workers=%d device=%s preset=%s",
        sha[:12],
        pdf_path.name,
        total_pages,
        BATCH_PAGES,
        len(batches),
        num_workers,
        resolved_device,
        preset,
    )

    # 1. Fast recovery of completed batches from artifacts
    recovered_by_i, pending_batches = _scan_and_recover_batches(
        batch_dir=batch_dir,
        batches=batches,
        resume=resume,
        log=log,
        sha=sha,
    )

    batch_results: list[dict] = list(recovered_by_i.values())
    total_chars = sum(int(b.get("chars", 0)) for b in batch_results)
    total_tables = sum(int(b.get("tables", 0)) for b in batch_results)
    seconds_start = time.perf_counter()

    lock = threading.Lock()

    def _checkpoint() -> None:
        with lock:
            res = _build_result(
                sha=sha,
                pdf_path=pdf_path,
                stored_pdf=stored_pdf,
                original_pdf=original_pdf,
                preset=preset,
                device=device,
                resolved_device=resolved_device,
                total_pages=total_pages,
                batches=batches,
                batch_results=batch_results,
                total_chars=total_chars,
                total_tables=total_tables,
                seconds_total=time.perf_counter() - seconds_start,
                batch_dir=batch_dir,
                result_json_path=result_json_path,
            )
            _write_json(result_json_path, res)

    # Initial checkpoint
    _checkpoint()

    # 2. Dispatch pending batches to parallel worker pool
    if pending_batches:
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            future_to_batch = {
                executor.submit(
                    _process_batch_with_fallbacks,
                    batch=batch,
                    preset=preset,
                    device=resolved_device,
                    batch_dir=batch_dir,
                    log=log,
                    batch_pos=batch["i"] + 1,
                    total_batches=len(batches),
                ): batch
                for batch in pending_batches
            }

            for future in concurrent.futures.as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    stats = future.result()
                except Exception as exc:
                    log.error(
                        "[batch %02d/%02d] unexpected worker exception: %s",
                        batch["i"] + 1,
                        len(batches),
                        exc,
                    )
                    stats = {
                        "i": batch["i"],
                        "pages": batch["pages"],
                        "path": batch["path"],
                        "preset_used": None,
                        "status": "failed_all_fallbacks",
                        "seconds": 0.0,
                        "chars": 0,
                        "tables": 0,
                        "ram_delta_mb": None,
                        "error": str(exc),
                        "cached": False,
                    }

                with lock:
                    batch_results.append(stats)
                    total_chars += int(stats.get("chars", 0))
                    total_tables += int(stats.get("tables", 0))

                _checkpoint()

    # 3. Final validation & ordered merge
    seconds_total = round(time.perf_counter() - seconds_start, 1)

    merge_result = merge_pdf_batch_outputs(batch_dir, batches)
    merged_md_path = Path(merge_result["outputs"]["merged_md"])
    merged_manifest_path = Path(merge_result["outputs"]["merged_manifest"])

    final_result = _build_result(
        sha=sha,
        pdf_path=pdf_path,
        stored_pdf=stored_pdf,
        original_pdf=original_pdf,
        preset=preset,
        device=device,
        resolved_device=resolved_device,
        total_pages=total_pages,
        batches=batches,
        batch_results=batch_results,
        total_chars=total_chars,
        total_tables=total_tables,
        seconds_total=seconds_total,
        batch_dir=batch_dir,
        result_json_path=result_json_path,
        merged_md_path=merged_md_path,
        merged_manifest_path=merged_manifest_path,
    )

    _write_json(result_json_path, final_result)

    log.info(
        "[done %s] pages=%d ok=%d failed=%d | batches=%d ok=%d failed=%d | %.1fs | %.1fk chars | %d tables",
        sha[:12],
        total_pages,
        final_result["totals"]["pages_ok"],
        final_result["totals"]["pages_failed"],
        final_result["document"]["total_batches"],
        final_result["totals"]["batches_ok"],
        final_result["totals"]["batches_failed"],
        final_result["totals"]["seconds_total"],
        final_result["totals"]["chars"] / 1000,
        final_result["totals"]["tables"],
    )

    return final_result
