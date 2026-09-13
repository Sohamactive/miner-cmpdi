"""PDF-only ingestion runner v1.

What it does:
1. fingerprint the PDF
2. store immutable upload copy
3. split into 3-page batches
4. run Docling batch-by-batch with a hard per-batch timeout
5. retry lighter presets on failure/timeout
6. save per-batch outputs and rolling result.json checkpoints
7. call pdf_merge.py to merge outputs
"""

from __future__ import annotations

import json
import multiprocessing as mp
import shutil
import time
import traceback
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

import pymupdf

from .config import BATCH_PAGES, resolve_device
from .logging_setup import setup_clean_logs
from .pdf_merge import merge_pdf_batch_outputs
from .pdf_splitter import sha256_of, split_pdf

TIMEOUTS_S = {
    "digital": 120,
    "scanned": 360,
    "light_table": 240,
    "ocr_only": 180,
}


def _page_count(pdf_path: Path) -> int:
    doc = pymupdf.open(pdf_path)
    total = len(doc)
    doc.close()
    return total


def _page_span_count(pages: str) -> int:
    """'1-3' -> 3, '10-10' -> 1"""
    start, end = pages.split("-")
    return int(end) - int(start) + 1


def _count_tables(doc_dict: dict) -> int:
    """Best-effort table count; exact shape can vary by Docling version."""
    tables = doc_dict.get("tables", [])
    return len(tables) if isinstance(tables, list) else 0


def _memory_mb() -> float | None:
    if psutil is None:
        return None
    proc = psutil.Process()
    return round(proc.memory_info().rss / (1024 * 1024), 1)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _batch_paths(batch_dir: Path, batch_index: int) -> dict[str, Path]:
    stem = f"batch_{batch_index:03d}"
    return {
        "md": batch_dir / f"{stem}.md",
        "json": batch_dir / f"{stem}.json",
        "stats": batch_dir / f"{stem}.stats.json",
    }


def _status_slug(status: object) -> str:
    return str(status).strip().lower().removeprefix("conversionstatus.")


def _is_completed_status(status: object) -> bool:
    return _status_slug(status) in {
        "success",
        "partial_success",
        "cached",
        "completed_from_artifacts",
    }


def _has_any_artifact(paths: dict[str, Path]) -> bool:
    return any(path.exists() for path in paths.values())


def _recover_batch_from_artifacts(
    batch: dict,
    paths: dict[str, Path],
) -> tuple[dict | None, str | None]:

    
    """Recover one completed batch from md/json/stats artifacts if they are trustworthy."""
    if not all(path.exists() for path in paths.values()):
        return None, "missing_artifacts"

    try:
        markdown = paths["md"].read_text(encoding="utf-8")
        doc_json = _read_json(paths["json"])
        stats = _read_json(paths["stats"])
    except Exception as exc:  # noqa: BLE001
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


def _worker_convert(batch: dict, preset: str, device: str, queue: mp.Queue) -> None:
    """Run one Docling conversion in a separate process for hard timeout control."""
    try:
        from .converter import get_converter
        from .logging_setup import setup_clean_logs

        setup_clean_logs(verbose=False)

        mem_before = _memory_mb()
        t0 = time.perf_counter()

        converter = get_converter(preset=preset, device=device)
        result = converter.convert(batch["path"])
        secs = round(time.perf_counter() - t0, 1)

        markdown = result.document.export_to_markdown()
        doc_dict = result.document.export_to_dict()

        mem_after = _memory_mb()
        mem_delta = None
        if mem_before is not None and mem_after is not None:
            mem_delta = round(mem_after - mem_before, 1)

        queue.put(
            {
                "ok": True,
                "stats": {
                    "i": batch["i"],
                    "pages": batch["pages"],
                    "path": batch["path"],
                    "preset_used": preset,
                    "status": str(result.status),
                    "seconds": secs,
                    "chars": len(markdown),
                    "tables": _count_tables(doc_dict),
                    "ram_delta_mb": mem_delta,
                    "error": None,
                    "cached": False,
                },
                "markdown": markdown,
                "doc_dict": doc_dict,
            }
        )

    except BaseException as exc:  # noqa: BLE001
        secs = round(time.perf_counter() - t0, 1) if "t0" in locals() else 0.0

        mem_after = _memory_mb()
        mem_delta = None
        if "mem_before" in locals() and mem_before is not None and mem_after is not None:
            mem_delta = round(mem_after - mem_before, 1)

        try:
            queue.put(
                {
                    "ok": False,
                    "stats": {
                        "i": batch["i"],
                        "pages": batch["pages"],
                        "path": batch["path"],
                        "preset_used": preset,
                        "status": "failed",
                        "seconds": secs,
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
            # If queue handoff itself fails, let the process exit non-zero.
            raise


def _run_one_batch(
    batch: dict, preset: str, device: str, timeout_s: int
) -> tuple[dict, str, dict | None, str | None]:
    """Run one batch with a hard timeout using a child process."""
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue()
    proc = ctx.Process(target=_worker_convert, args=(batch, preset, device, queue))
    started = time.perf_counter()
    proc.start()
    proc.join(timeout_s)

    if proc.is_alive():
        proc.terminate()
        proc.join(10)
        stats = {
            "i": batch["i"],
            "pages": batch["pages"],
            "path": batch["path"],
            "preset_used": preset,
            "status": "timeout",
            "seconds": float(timeout_s),
            "chars": 0,
            "tables": 0,
            "ram_delta_mb": None,
            "error": f"hard timeout after {timeout_s}s",
            "cached": False,
        }
        return stats, "", None, stats["error"]

    if proc.exitcode not in (0, None) and queue.empty():
        elapsed = round(time.perf_counter() - started, 1)
        stats = {
            "i": batch["i"],
            "pages": batch["pages"],
            "path": batch["path"],
            "preset_used": preset,
            "status": "failed",
            "seconds": elapsed,
            "chars": 0,
            "tables": 0,
            "ram_delta_mb": None,
            "error": f"worker exited with code {proc.exitcode}",
            "cached": False,
        }
        return stats, "", None, stats["error"]

    payload = queue.get() if not queue.empty() else {
        "ok": False,
        "stats": {
            "i": batch["i"],
            "pages": batch["pages"],
            "path": batch["path"],
            "preset_used": preset,
            "status": "failed",
            "seconds": 0.0,
            "chars": 0,
            "tables": 0,
            "ram_delta_mb": None,
            "error": "worker exited without payload",
            "cached": False,
        },
        "markdown": "",
        "doc_dict": None,
        "error": "worker exited without payload",
    }
    err = payload.get("error") if not payload.get("ok") else None
    trace = payload.get("traceback")
    if trace:
        err = f"{err}\n{trace}"
    return payload["stats"], payload["markdown"], payload["doc_dict"], err


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
        "batches": batch_results,
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
            "merged_manifest": str(merged_manifest_path) if merged_manifest_path else None,
            "merge_result": str(batch_dir / "merge_result.json"),
            "result_json": str(result_json_path),
            "run_log": str(batch_dir / "run.log"),
        },
    }


def _checkpoint_result(result_json_path: Path, payload: dict) -> None:
    _write_json(result_json_path, payload)


def run_pdf(
    pdf_path: str | Path,
    preset: str = "scanned",
    device: str = "auto",
    verbose: bool = False,
    resume: bool = True,
) -> dict:
    """Process one PDF sequentially and return full stats."""
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

    batches = split_pdf(original_pdf, batch_dir, batch_pages=BATCH_PAGES)

    previous_result = _read_json(result_json_path) if resume else None
    recovered_batches_by_i: dict[int, dict] = {}
    needs_rebuild = 0
    pending = 0
    for batch in batches:
        paths = _batch_paths(batch_dir, batch["i"])
        recovered, reason = _recover_batch_from_artifacts(batch, paths)
        if recovered is not None:
            recovered_batches_by_i[batch["i"]] = recovered
        elif _has_any_artifact(paths):
            needs_rebuild += 1
            log.warning(
                "[resume %s] pp %s artifacts incomplete -> rebuild (%s)",
                sha[:12],
                batch["pages"],
                reason,
            )
        else:
            pending += 1

    if previous_result is not None and recovered_batches_by_i:
        log.info(
            "[resume %s] recovered=%d pending=%d rebuild=%d from batch artifacts (result.json reconciled)",
            sha[:12],
            len(recovered_batches_by_i),
            pending,
            needs_rebuild,
        )
    elif recovered_batches_by_i:
        log.info(
            "[resume %s] recovered=%d pending=%d rebuild=%d from batch artifacts",
            sha[:12],
            len(recovered_batches_by_i),
            pending,
            needs_rebuild,
        )

    log.info(
        "[ingest %s] file=%s total_pages=%d batch_size=%d total_batches=%d device=%s preset=%s",
        sha[:12],
        pdf_path.name,
        total_pages,
        BATCH_PAGES,
        len(batches),
        resolved_device,
        preset,
    )

    batch_results: list[dict] = []
    total_chars = 0
    total_tables = 0
    seconds_start = time.perf_counter()

    _checkpoint_result(
        result_json_path,
        _build_result(
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
            seconds_total=0.0,
            batch_dir=batch_dir,
            result_json_path=result_json_path,
        ),
    )

    for batch_pos, batch in enumerate(batches, start=1):
        paths = _batch_paths(batch_dir, batch["i"])
        recovered_batch = recovered_batches_by_i.get(batch["i"])

        if (
            resume
            and recovered_batch is not None
        ):
            cached_stats = dict(recovered_batch)
            cached_stats["cached"] = True

            batch_results.append(cached_stats)
            total_chars += int(cached_stats.get("chars", 0))
            total_tables += int(cached_stats.get("tables", 0))

            log.info(
                "[batch %02d/%02d] pp %s .... recovered %.1fs | %.1fk chars | %d tables | %s",
                batch_pos,
                len(batches),
                batch["pages"],
                float(cached_stats.get("seconds", 0.0)),
                float(cached_stats.get("chars", 0)) / 1000,
                int(cached_stats.get("tables", 0)),
                resolved_device,
            )
            _checkpoint_result(
                result_json_path,
                _build_result(
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
                ),
            )
            continue

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
            timeout_s = TIMEOUTS_S[attempt_preset]
            log.info(
                "[batch %02d/%02d] START pp %s preset=%s timeout=%ss",
                batch_pos,
                len(batches),
                batch["pages"],
                attempt_preset,
                timeout_s,
            )
            stats, markdown, doc_dict, err = _run_one_batch(
                batch=batch,
                preset=attempt_preset,
                device=resolved_device,
                timeout_s=timeout_s,
            )

            if err is None:
                final_stats = stats
                final_markdown = markdown
                final_doc_dict = doc_dict
                break

            log.error(
                "[batch %02d/%02d] pp %s FAILED with %s after %.1fs: %s",
                batch_pos,
                len(batches),
                batch["pages"],
                attempt_preset,
                stats["seconds"],
                err,
            )

        if final_stats is None:
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
                "error": "all fallback presets failed",
                "cached": False,
            }
            _write_json(paths["stats"], final_stats)
            batch_results.append(final_stats)

            log.error(
                "[batch %02d/%02d] pp %s .... failed_all_fallbacks",
                batch_pos,
                len(batches),
                batch["pages"],
            )
            _checkpoint_result(
                result_json_path,
                _build_result(
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
                ),
            )
            continue

        batch_results.append(final_stats)
        total_chars += final_stats["chars"]
        total_tables += final_stats["tables"]

        paths["md"].write_text(final_markdown, encoding="utf-8")
        if final_doc_dict is not None:
            _write_json(paths["json"], final_doc_dict)
        _write_json(paths["stats"], final_stats)

        ram_text = (
            f" | +{final_stats['ram_delta_mb']}MB"
            if final_stats["ram_delta_mb"] is not None
            else ""
        )

        log.info(
            "[batch %02d/%02d] pp %s .... %s %.1fs | %.1fk chars | %d tables | %s%s",
            batch_pos,
            len(batches),
            batch["pages"],
            final_stats["status"],
            final_stats["seconds"],
            final_stats["chars"] / 1000,
            final_stats["tables"],
            resolved_device,
            ram_text,
        )

        _checkpoint_result(
            result_json_path,
            _build_result(
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
            ),
        )

    seconds_total = round(time.perf_counter() - seconds_start, 1)

    merge_result = merge_pdf_batch_outputs(batch_dir, batches)
    merged_md_path = Path(merge_result["outputs"]["merged_md"])
    merged_manifest_path = Path(merge_result["outputs"]["merged_manifest"])

    result = _build_result(
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

    _checkpoint_result(result_json_path, result)

    log.info(
        "[done %s] pages=%d ok=%d failed=%d | batches=%d ok=%d failed=%d | %.1fs | %.1fk chars | %d tables",
        sha[:12],
        total_pages,
        result["totals"]["pages_ok"],
        result["totals"]["pages_failed"],
        result["document"]["total_batches"],
        result["totals"]["batches_ok"],
        result["totals"]["batches_failed"],
        result["totals"]["seconds_total"],
        result["totals"]["chars"] / 1000,
        result["totals"]["tables"],
    )

    return result
