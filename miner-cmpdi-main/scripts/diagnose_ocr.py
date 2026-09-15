"""OCR diagnostic for "PARTIAL_SUCCESS with 0 chars" failures.

Standalone tool (NOT part of the ingestion pipeline): runs
config.scanned_opts() through converter.get_converter() directly, OUTSIDE the
multiprocessing/timeout harness in pdf_runner.py, so EasyOCR exceptions and
warnings surface directly on stdout/stderr instead of being serialized
through the worker queue.

Usage (from backend/, uv only):
    uv run python ../scripts/diagnose_ocr.py data/batches/<sha>/batch_000.pdf
    uv run python ../scripts/diagnose_ocr.py 1984.pdf --page 2
    uv run python ../scripts/diagnose_ocr.py data/batches/<sha>/batch_000.pdf --rasterize-only

Sections: device report -> model-file report -> rasterized PNG (+ blank check)
-> direct (no-subprocess) Docling conversion -> findings summary.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
import warnings
from pathlib import Path

# Resolve backend/ on sys.path so this runs from anywhere (repo-root scripts/).
_BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def check_device(device_arg: str) -> dict:
    """Report GPU-requested vs GPU-available and the EasyOCR device path."""
    import torch

    from app.ingestion import config

    resolved = config.resolve_device(device_arg)
    opts = config.scanned_opts(device_arg)
    ocr = opts.ocr_options
    info = {
        "device_arg": device_arg,
        "DOCLING_DEVICE": os.getenv("DOCLING_DEVICE", ""),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "resolved_device": resolved,
        "accelerator_device": str(opts.accelerator_options.device),
        "num_threads": opts.accelerator_options.num_threads,
        "ocr_langs": list(config.OCR_LANGS),
        "easyocr_use_gpu": getattr(ocr, "use_gpu", None),
        "images_scale": config.IMAGES_SCALE,
    }
    print("== device ==")
    for key, val in info.items():
        print(f"  {key}: {val}")
    if resolved == "cpu" and not torch.cuda.is_available():
        print("  note: CPU-only torch; EasyOCR will run on CPU (slow but functional).")
    return info


def check_models(langs: list[str]) -> dict:
    """Verify EasyOCR model files exist and are loadable (not partial downloads).

    EasyOCR publishes no checksums, so "present + nonzero + torch.load parses"
    is the strongest local integrity signal available.
    """
    import torch

    model_dir = Path(
        os.getenv("EASYOCR_MODULE_PATH", Path.home() / ".EasyOCR" / "model")
    )
    # Detection model is fixed ("craft"); recognition model depends on langs.
    expected = {"craft_mlt_25k", "english_g2" if "en" in langs else "latin_g2"}
    status: dict = {"model_dir": str(model_dir), "files": {}}
    print("== easyocr models ==")
    print(f"  dir: {model_dir} (exists={model_dir.is_dir()})")
    if model_dir.is_dir():
        for child in sorted(model_dir.iterdir()):
            tag = ""
            if child.suffix == ".tmp" or child.stat().st_size == 0:
                tag = "  <-- SUSPECT: partial/empty download"
            print(f"  {child.name}  {child.stat().st_size / 1e6:.1f} MB{tag}")
            status["files"][child.name] = child.stat().st_size
    missing = [f"{name}.pth" for name in sorted(expected)]
    missing = [m for m in missing if m not in status["files"]]
    for name in sorted(expected):
        path = model_dir / f"{name}.pth"
        if not path.exists():
            print(f"  MISSING: {path.name} (expected for langs={langs})")
            status["files"][path.name] = -1
            continue
        try:
            payload = torch.load(str(path), map_location="cpu", weights_only=True)
            n_tensors = (
                len(payload) if isinstance(payload, dict) else "non-dict-payload"
            )
            print(f"  {path.name}: torch.load OK ({n_tensors} tensors)")
            status["files"][path.name + ":load"] = "ok"
        except Exception as exc:
            print(f"  {path.name}: torch.load FAILED: {exc}")
            status["files"][path.name + ":load"] = f"FAILED: {exc}"
    if missing:
        print(f"  note: missing files download on first Reader init (needs network).")
    return status


def rasterize_page(pdf_path: Path, page_idx: int, png_out: Path) -> dict:
    """Render one page at config IMAGES_SCALE and check it is not blank."""
    import pymupdf

    from app.ingestion import config

    doc = pymupdf.open(pdf_path)
    page = doc[page_idx]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(config.IMAGES_SCALE, config.IMAGES_SCALE))
    pix.save(png_out)
    doc.close()

    import statistics

    samples = list(pix.samples)
    mean = statistics.fmean(samples)
    std = statistics.pstdev(samples) if len(samples) > 1 else 0.0
    nonwhite = sum(1 for b in samples if b < 250) / max(1, len(samples))
    info = {
        "png": str(png_out),
        "size": f"{pix.width}x{pix.height}",
        "mean_brightness": round(mean, 1),
        "std": round(std, 1),
        "nonwhite_frac": round(nonwhite, 4),
    }
    print("== raster ==")
    for key, val in info.items():
        print(f"  {key}: {val}")
    if std < 1.0 or nonwhite < 0.001:
        print("  VERDICT: raster looks BLANK — suspect rasterization bug, not OCR.")
    else:
        print("  VERDICT: raster has content — EasyOCR is being fed real pixels.")
    return info


def run_direct_convert(target: Path, preset: str, device_arg: str) -> dict:
    """Convert directly (no subprocess): exceptions/warnings stay visible."""
    from app.ingestion.converter import get_converter

    print("== direct convert ==")
    print(f"  file: {target}  preset={preset}  device_arg={device_arg}")
    caught: list[warnings.WarningMessage] = []
    t0 = time.perf_counter()
    try:
        with warnings.catch_warnings(record=True) as caught_list:
            warnings.simplefilter("always")
            converter = get_converter(preset=preset, device=device_arg)
            result = converter.convert(str(target))
        caught = list(caught_list)
    except Exception as exc:
        secs = round(time.perf_counter() - t0, 1)
        print(f"  RAISED after {secs}s: {type(exc).__name__}: {exc}")
        raise
    secs = round(time.perf_counter() - t0, 1)
    markdown = result.document.export_to_markdown()
    try:
        tables = result.document.export_to_dict().get("tables", [])
        n_tables = len(tables) if isinstance(tables, list) else 0
    except Exception:
        n_tables = -1
    print(f"  status: {result.status}  seconds: {secs}")
    print(f"  markdown_len: {len(markdown)}  tables: {n_tables}")
    print(f"  head200: {markdown[:200]!r}")
    print(f"  warnings captured: {len(caught)}")
    for wmn in caught[:10]:
        print(f"    {wmn.category.__name__}: {str(wmn.message)[:200]}")
    if not markdown.strip():
        print("  VERDICT: empty markdown — reproduces the 0-chars failure.")
    return {"status": str(result.status), "seconds": secs, "chars": len(markdown)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path, help="PDF page file or batch_XXX.pdf")
    ap.add_argument("--page", type=int, default=1, help="1-based page to diagnose")
    ap.add_argument("--preset", default="scanned")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--png-out", type=Path, default=None, help="raster PNG path")
    ap.add_argument("--rasterize-only", action="store_true")
    ap.add_argument("--skip-convert", action="store_true")
    ap.add_argument("--skip-models", action="store_true")
    args = ap.parse_args()

    if not args.input.exists():
        print(f"input not found: {args.input}", file=sys.stderr)
        return 2

    from app.ingestion import config  # noqa: E402  (needs sys.path fix above)

    print(f"# diagnose_ocr: {args.input} page={args.page} preset={args.preset}")

    device_info = check_device(args.device)
    model_info = {} if args.skip_models else check_models(list(config.OCR_LANGS))

    import pymupdf  # noqa: E402

    doc = pymupdf.open(args.input)
    npages = len(doc)
    doc.close()
    if not 1 <= args.page <= npages:
        print(f"--page {args.page} out of range (1..{npages})", file=sys.stderr)
        return 2

    png_out = args.png_out or args.input.with_name(
        f"{args.input.stem}.diag_p{args.page}.png"
    )
    target = args.input
    tmpdir = None
    if npages > 1:
        # Isolate the single page: matches "takes one PDF page" and keeps CPU
        # inference fast while reproducing per-page OCR behavior.
        tmpdir = tempfile.TemporaryDirectory(prefix="diag_ocr_")
        target = Path(tmpdir.name) / f"page{args.page}.pdf"
        src = pymupdf.open(args.input)
        one = pymupdf.open()
        one.insert_pdf(src, from_page=args.page - 1, to_page=args.page - 1)
        one.save(target)
        one.close()
        src.close()
        print(f"  extracted page {args.page}/{npages} -> {target}")

    raster_info = rasterize_page(target, 0, png_out)

    convert_info: dict = {}
    if not (args.rasterize_only or args.skip_convert):
        try:
            convert_info = run_direct_convert(target, args.preset, args.device)
        finally:
            pass

    print("== findings ==")
    empty = convert_info.get("chars", None) == 0
    loads_ok = all(
        v != "FAILED" and not str(v).startswith("FAILED")
        for k, v in model_info.get("files", {}).items()
        if k.endswith(":load")
    )
    print(f"  models_present_and_loadable: {bool(model_info) and loads_ok}")
    print(f"  raster_has_content: {raster_info['std'] >= 1.0}")
    print(f"  direct_convert_chars: {convert_info.get('chars', 'skipped')}")
    if convert_info and empty and raster_info["std"] >= 1.0 and loads_ok:
        print("  suspect: OCR inference returning no text regions on legible "
              "pixels with healthy models — check EasyOCR detector output "
              "thresholds/logging next, not models or rasterizer.")
    elif convert_info and empty and raster_info["std"] < 1.0:
        print("  suspect: rasterization bug (blank image fed to OCR).")
    elif convert_info and empty and not loads_ok:
        print("  suspect: broken/missing OCR model files.")

    if tmpdir is not None:
        tmpdir.cleanup()
    _ = device_info
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
