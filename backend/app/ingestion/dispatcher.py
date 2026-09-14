"""Unified Document Ingestion Dispatcher.

Routes inputs (PDF, XLSX, XLS, CSV, PNG, JPG, JPEG, TIFF) to the appropriate
runner while guaranteeing a unified output artifact contract.
"""

from __future__ import annotations

from pathlib import Path

from .image_runner import run_image
from .pdf_runner import run_pdf
from .table_runner import run_table

PDF_EXTENSIONS = {".pdf"}
SPREADSHEET_EXTENSIONS = {".xlsx", ".xls", ".csv"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
SUPPORTED_EXTENSIONS = PDF_EXTENSIONS | SPREADSHEET_EXTENSIONS | IMAGE_EXTENSIONS


def get_supported_extensions() -> set[str]:
    """Return set of all supported file extensions."""
    return set(SUPPORTED_EXTENSIONS)


def run_ingest(
    file_path: str | Path,
    preset: str | None = None,
    device: str = "auto",
    verbose: bool = False,
    resume: bool = True,
    max_workers: int | None = None,
    auto_detect: bool = True,
) -> dict:
    """Unified entry point for document ingestion.

    Inspects file extension and dispatches to PDF, Spreadsheet, or Image runner.
    preset=None means "no explicit choice" (PDF default "scanned" with text-layer
    auto-detection when auto_detect is on); a preset name forces that start.
    auto_detect=False restores the legacy forced-start behavior for PDFs.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Document not found: {file_path}")

    ext = file_path.suffix.lower()
    if ext in PDF_EXTENSIONS:
        return run_pdf(
            pdf_path=file_path,
            preset=preset,
            device=device,
            verbose=verbose,
            resume=resume,
            max_workers=max_workers,
            auto_detect=auto_detect,
        )
    elif ext in SPREADSHEET_EXTENSIONS:
        return run_table(
            file_path=file_path,
            preset=preset if preset is not None else "scanned",
            device=device,
            verbose=verbose,
            resume=resume,
        )
    elif ext in IMAGE_EXTENSIONS:
        return run_image(
            image_path=file_path,
            preset=preset if preset is not None else "scanned",
            device=device,
            verbose=verbose,
            resume=resume,
            max_workers=max_workers,
        )
    else:
        raise ValueError(
            f"Unsupported file format '{ext}'. Supported formats: {sorted(SUPPORTED_EXTENSIONS)}"
        )
