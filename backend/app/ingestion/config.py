"""Ingestion presets v1 — PDF-only. CPU now, CUDA later via device='auto'."""

from __future__ import annotations

import os

import torch
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.pipeline_options import (
    EasyOcrOptions,
    PdfPipelineOptions,
    TableFormerMode,
    TableStructureOptions,
)

# ---- tuning ---------------------------------------------------------------
# BATCH_PAGES: pages per sub-batch sent to Docling at once.
#   Keep at 3; larger batches hit 16 GB RAM limits with EasyOCR.
BATCH_PAGES = 3

MAX_WORKERS = int(os.getenv("INGESTION_MAX_WORKERS", "2"))
NUM_THREADS = min(8, max(1, (os.cpu_count() or 8) // max(1, MAX_WORKERS)))
IMAGES_SCALE = 1.5
OCR_BATCH = 2
LAYOUT_BATCH = 4
TABLE_BATCH = 2
OCR_LANGS = ["en"]

# DIGITAL_TEXT_*: cheap born-digital detector tuning (see _has_digital_text_layer
# in pdf_runner.py). A sampled page's non-whitespace chars from
# page.get_text("text"), averaged over DIGITAL_TEXT_SAMPLE_PAGES pages; average
# at/above DIGITAL_TEXT_CHAR_THRESHOLD means a real text layer is present.
DIGITAL_TEXT_SAMPLE_PAGES = 5
DIGITAL_TEXT_CHAR_THRESHOLD = 100.0

# TIMEOUTS_S: per-preset hard kill timeout in seconds.
#
# "digital"    - pure text extraction, no OCR/TableFormer. Fast; 120s is plenty.
# "scanned"    - EasyOCR + ACCURATE TableFormer on raster pages. Inherently slow
#                on 1980s archival scans; give it 360s (6 min) before giving up.
#                NOTE: if it still hangs, the page structure is genuinely
#                unsolvable by Docling and PyMuPDF fallback will recover text.
# "light_table"- fast path (FAST TableFormer). If it doesn't finish in 150s it
#                won't finish at all — fall through quickly to ocr_only.
# "ocr_only"   - EasyOCR without TableFormer. Should be fast, but EasyOCR can
#                hang on badly corrupted rasters; 240s is a safe upper bound.
TIMEOUTS_S = {
    "digital":     120,   # no OCR / TableFormer
    "scanned":     360,   # OCR + ACCURATE tables — give it real time
    "light_table": 150,   # FAST tables — bail quickly if stuck
    "ocr_only":    240,   # OCR alone — generous for bad rasters
}

def doc_timeout_for(preset: str) -> float | None:
    """Internal Docling document_timeout per preset.

    Must stay *below* the external hard kill in TIMEOUTS_S so Docling
    self-aborts (returns PARTIAL_SUCCESS) instead of hanging until the
    subprocess harness has to terminate() it. terminate() on Windows
    with torch/EasyOCR loaded can stall; a cooperative internal abort
    is always cleaner. Buffer is ~30s (min 60s) for payload delivery.
    """
    hard = TIMEOUTS_S.get(preset, 180)
    return float(max(60, hard - 30))


def resolve_device(prefer: str = "auto") -> str:
    """DOCLING_DEVICE env_device > prefer > cuda-if-available > cpu."""
    valid_devices = {"cuda", "cpu", "mps"}  # Added mps for Apple Silicon support

    # 1. Check environment variable
    env = os.getenv("DOCLING_DEVICE", "").strip().lower()
    if env in valid_devices:
        return env

    # 2. Check the preference parameter
    prefer_clean = prefer.strip().lower()
    if prefer_clean in valid_devices:
        return prefer_clean

    # 3. Fallback to auto-detection
    return "cuda" if torch.cuda.is_available() else "cpu"


def _base(device: str, doc_timeout: float | None = None) -> PdfPipelineOptions:

    accel = AcceleratorOptions(
        num_threads=int(os.getenv("DOCLING_NUM_THREADS", NUM_THREADS)),
        device=AcceleratorDevice(device),
    )

    return PdfPipelineOptions(
        do_table_structure=True,
        do_code_enrichment=False,
        do_formula_enrichment=False,
        do_picture_classification=False,
        do_picture_description=False,
        generate_page_images=False,
        images_scale=IMAGES_SCALE,
        ocr_batch_size=OCR_BATCH,
        layout_batch_size=LAYOUT_BATCH,
        table_batch_size=TABLE_BATCH,
        # Cooperative internal cap: Docling aborts itself when elapsed
        # exceeds this (returns PARTIAL_SUCCESS instead of hanging).
        # The real hard kill is still enforced externally by the subprocess
        # harness in pdf_runner.py (_run_one_batch: poll + terminate/kill
        # per TIMEOUTS_S). Internal value is always ~30s below the hard
        # kill so there is time to deliver the payload through the queue.
        document_timeout=doc_timeout,
        table_structure_options=TableStructureOptions(
            do_cell_matching=True,
            mode=TableFormerMode.ACCURATE,
        ),
        accelerator_options=accel,
    )


def scanned_opts(device: str = "auto") -> PdfPipelineOptions:
    """1984 scans: OCR on. EasyOCR use_gpu=None => auto (CPU now, GPU later)."""
    o = _base(resolve_device(device), doc_timeout_for("scanned"))
    o.do_ocr = True
    o.force_backend_text = False
    o.ocr_options = EasyOcrOptions(lang=list(OCR_LANGS), use_gpu=None)
    return o


def digital_opts(device: str = "auto") -> PdfPipelineOptions:
    """Modern PDFs with text layer: skip OCR, fast."""
    o = _base(resolve_device(device), doc_timeout_for("digital"))
    o.do_ocr = False
    o.force_backend_text = True
    return o


def light_table_opts(device: str = "auto") -> PdfPipelineOptions:
    """Fallback 1: FAST tables, no cell matching (broken 1984 tables)."""
    o = scanned_opts(device)
    o.document_timeout = doc_timeout_for("light_table")
    o.table_structure_options = TableStructureOptions(
        do_cell_matching=False, mode=TableFormerMode.FAST
    )
    return o


def ocr_only_opts(device: str = "auto") -> PdfPipelineOptions:
    """Fallback 2: text only, tables off (worst pages still yield evidence)."""

    o = scanned_opts(device)
    o.document_timeout = doc_timeout_for("ocr_only")
    o.do_table_structure = False
    return o
