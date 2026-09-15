"""Image Ingestion Runner (PNG, JPG, JPEG, TIFF, BMP, WEBP).

Converts standalone images into a standard 1-page PDF working copy and processes
via run_pdf() to leverage the full Docling OCR and TableFormer pipeline.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pymupdf

from .pdf_runner import run_pdf
from .pdf_splitter import sha256_of


def run_image(
    image_path: str | Path,
    preset: str = "scanned",
    device: str = "auto",
    verbose: bool = False,
    resume: bool = True,
    max_workers: int | None = None,
) -> dict:
    """Process a standalone image by wrapping it into a 1-page PDF and calling run_pdf."""
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    sha = sha256_of(image_path)
    ext = image_path.suffix.lower()

    uploads_dir = Path("data") / "uploads"
    batch_dir = Path("data") / "batches" / sha
    uploads_dir.mkdir(parents=True, exist_ok=True)
    batch_dir.mkdir(parents=True, exist_ok=True)

    # Store immutable upload copy of original image
    stored_image = uploads_dir / f"{sha}{ext}"
    if not stored_image.exists():
        shutil.copy2(image_path, stored_image)

    # Convert image to a 1-page PDF working copy
    pdf_working_path = batch_dir / "original.pdf"
    if not pdf_working_path.exists():
        img_doc = pymupdf.open(image_path)
        pdf_bytes = img_doc.convert_to_pdf()
        img_doc.close()

        pdf_doc = pymupdf.open("pdf", pdf_bytes)
        pdf_doc.save(pdf_working_path)
        pdf_doc.close()

    # Run standard PDF pipeline on the 1-page PDF
    result = run_pdf(
        pdf_path=pdf_working_path,
        preset=preset,
        device=device,
        verbose=verbose,
        resume=resume,
        max_workers=max_workers or 1,
    )

    # Update document metadata to reflect original image
    result["document"]["source_path"] = str(image_path)
    result["document"]["filename"] = image_path.name
    result["document"]["format"] = ext.removeprefix(".")

    # Update result.json with the image source info
    result_json_path = batch_dir / "result.json"
    if result_json_path.exists():
        import json
        result_json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    return result
