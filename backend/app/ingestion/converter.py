"""Singleton DocumentConverter per preset. Models load once per process."""

from __future__ import annotations

from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption

from . import config

_cache: dict[str, DocumentConverter] = {}


def get_converter(preset: str = "scanned", device: str = "auto") -> DocumentConverter:
    """preset: scanned | digital | light_table | ocr_only. Cached per (preset, device)."""
    key = f"{preset}:{config.resolve_device(device)}"
    if key not in _cache:
        makers = {
            "scanned": config.scanned_opts,
            "digital": config.digital_opts,
            "light_table": config.light_table_opts,
            "ocr_only": config.ocr_only_opts,
        }
        opts = makers[preset](device)
        _cache[key] = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
        )
    return _cache[key]


def clear_cache() -> None:
    _cache.clear()
