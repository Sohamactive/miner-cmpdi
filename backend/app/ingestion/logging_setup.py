"""Clean logs: quiet console + loud file. Nothing lost."""
from __future__ import annotations

import logging
import os
import sys
import warnings
from pathlib import Path

_QUIET = ("transformers", "huggingface_hub", "docling",
          "easyocr", "rapidocr", "torch", "PIL", "tokenizers")

def setup_clean_logs(verbose: bool = False, log_file: str | Path | None = None) -> logging.Logger:
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    # kills your 40x tied-weights + RTDetr + HF-hub spam
    for pat in (r".*tied weights.*", r".*RTDetrImageProcessor.*",
                r".*unauthenticated.*", r".*use_fast=False.*",
                r".*pin_memory.*no accelerator is found.*",
                r".*torch\.quantize_per_tensor.*deprecated.*"):
        warnings.filterwarnings("ignore", message=pat)

    for name in _QUIET:  # libs: errors only (failures still show)
        logging.getLogger(name).setLevel(logging.ERROR)

    log = logging.getLogger("miner.ingestion")
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    log.handlers.clear()
    log.propagate = False

    # console: one-liners only
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG if verbose else logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(ch)

    # file: complete record (never truncated like Kaggle console)
    if log_file:
        p = Path(log_file); p.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(p, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s: %(message)s"))
        log.addHandler(fh)

    # Docling's own per-stage timings -> file only, only when debugging
    if verbose:
        from docling.datamodel.settings import settings
        settings.debug.profile_pipeline_timings = True
    return log

def get_logger() -> logging.Logger:
    return logging.getLogger("miner.ingestion")
