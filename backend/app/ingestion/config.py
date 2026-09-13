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

# ---- tuning----
BATCH_PAGES = 3
BATCH_TIMEOUT_S = 180  # 3 MINUTES
NUM_THREADS = 8
IMAGES_SCALE = 1.5
OCR_BATCH = 2
LAYOUT_BATCH = 4
TABLE_BATCH = 2
OCR_LANGS = ["en"]

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


def _base(device: str) -> PdfPipelineOptions:

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
        document_timeout=float(BATCH_TIMEOUT_S),
        table_structure_options=TableStructureOptions(
            do_cell_matching=True,
            mode=TableFormerMode.ACCURATE,
        ),
        accelerator_options=accel,
    )


def scanned_opts(device: str = "auto") -> PdfPipelineOptions:
    """1984 scans: OCR on. EasyOCR use_gpu=None => auto (CPU now, GPU later)."""
    o = _base(resolve_device(device))
    o.do_ocr = True
    o.force_backend_text = False
    o.ocr_options = EasyOcrOptions(lang=list(OCR_LANGS), use_gpu=None)
    return o


def digital_opts(device: str = "auto") -> PdfPipelineOptions:
    """Modern PDFs with text layer: skip OCR, fast."""
    o = _base(resolve_device(device))
    o.do_ocr = False
    o.force_backend_text = True
    return o


def light_table_opts(device: str = "auto") -> PdfPipelineOptions:
    """Fallback 1: FAST tables, no cell matching (broken 1984 tables)."""
    o = scanned_opts(device)
    o.table_structure_options = TableStructureOptions(
        do_cell_matching=False, mode=TableFormerMode.FAST
    )
    return o


def ocr_only_opts(device: str = "auto") -> PdfPipelineOptions:
    """Fallback 2: text only, tables off (worst pages still yield evidence)."""

    o = scanned_opts(device)
    o.do_table_structure = False
    return o
