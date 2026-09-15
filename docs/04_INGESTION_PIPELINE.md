# 04 — Ingestion Pipeline (Multi-Modal v1.1, implemented)

> Status: IMPLEMENTED with parallel batch worker pool, PyMuPDF emergency salvage for hard pages, and multi-modal support (PDF, XLSX/CSV, Images).
> Read after: `03_ARCHITECTURE.md` §2 + §7. Source of truth for `backend/app/ingestion/` behavior.

## 1. What it does (30 sec)

1. Upload PDF, XLSX/CSV, or Image → sha256 = `doc_id`
2. Dispatches via `dispatcher.py`:
   - PDFs: split into 3-page batches (`BATCH_PAGES=3`)
   - Spreadsheets: parsed sheet-by-sheet into Markdown tables & AST (`table_runner.py`)
   - Images: converted to 1-page PDF working copy (`image_runner.py`)
3. For PDFs: converts batches in **parallel** (`MAX_WORKERS=2` default via `ThreadPoolExecutor`)
4. Retry lighter presets on failure (`scanned` → `light_table` → `ocr_only`)
5. **Emergency PyMuPDF Fallback**: if Docling crashes (`0xC0000005`) or times out, native C PyMuPDF extracts text & tables (`status="partial_fallback_pymupdf"`) so zero pages are lost!
6. Write per-batch `.md` / `.json` / `.stats.json` + rolling `result.json`
7. Merge into `merged.md` + `merged_manifest.json` in strictly sequential order

Run it:

```powershell
cd backend
uv run uvicorn app.main:app --reload
# open http://localhost:8000/docs
# POST /api/documents/upload → POST /api/documents/{doc_id}/process
```

## 2. File map

| File | Owns |
|---|---|
| `app/ingestion/config.py` | Presets, `MAX_WORKERS`, `NUM_THREADS`, `TIMEOUTS_S`, Docling `PdfPipelineOptions` |
| `app/ingestion/dispatcher.py` | Unified entrypoint: routes PDF, Spreadsheet, Image inputs |
| `app/ingestion/pdf_splitter.py` | `sha256_of()`, `split_pdf()` via PyMuPDF. No Docling here |
| `app/ingestion/converter.py` | `get_converter(preset, device)` singleton cache per process |
| `app/ingestion/pdf_runner.py` | Modular orchestrator: parallel thread pool, isolated child processes, emergency PyMuPDF fallback, resume, checkpoints |
| `app/ingestion/table_runner.py` | Spreadsheet parser (.xlsx, .xls, .csv) into clean Markdown tables & AST |
| `app/ingestion/image_runner.py` | Image parser (.png, .jpg, .tiff) wrapping to 1-page PDF |
| `app/ingestion/pdf_merge.py` | `merge_pdf_batch_outputs()`: validate + `merged.md` + `merged_manifest.json` |
| `app/ingestion/logging_setup.py` | Quiet console (one-liners) + loud `run.log`; warning filters |
| `app/api/documents.py` | Thin routes only: `upload`, `{doc_id}/process`, `result`, `merged.md` |
| `app/main.py` | `create_app()`, mounts documents router at `/api/documents` |

Rule: routes never contain conversion logic. All Docling lives under `ingestion/`.

## 3. Presets

Defined in `config.py`. Device resolves `DOCLING_DEVICE` env > `device` arg > cuda-if-available > cpu. Laptop today → `cpu`.

| Preset | OCR | Tables | When used |
|---|---|---|---|
| `scanned` | ON (EasyOCR) | ACCURATE + cell matching | Default for 1984 scans; first attempt |
| `digital` | OFF + `force_backend_text` | ACCURATE | Modern text-layer PDFs (not yet default via API) |
| `light_table` | ON | FAST, no cell matching | Fallback 1: broken 1984 tables |
| `ocr_only` | ON | OFF | Fallback 2: worst pages still yield text |

Fallback chain in `pdf_runner.py`:

- requested `scanned` → `scanned → light_table → ocr_only`
- requested `digital` → `digital → scanned → light_table → ocr_only`

Tuning constants (`config.py`): `NUM_THREADS=8`, `IMAGES_SCALE=1.5`, `OCR_BATCH=2`, `LAYOUT_BATCH=4`, `TABLE_BATCH=2`, `OCR_LANGS=["en"]`.

## 4. Batching + timeouts

- Split: `split_pdf(src, batch_dir, batch_pages=3)` → `batch_000.pdf … batch_021.pdf` for 66pp.
- Run: sequential, one batch at a time. No parallelism in v1.
- Isolation: each batch runs in a `spawn` subprocess (`_worker_convert`).
- Hard timeouts (`pdf_runner.py:TIMEOUTS_S`): `digital=120s`, `scanned=360s`, `light_table=240s`, `ocr_only=180s`. Child is `terminate()`d on expiry. Docling `document_timeout` is soft only — the subprocess kill is the real timeout.
- Success = child returns payload with `err is None` (covers `SUCCESS` and `PARTIAL_SUCCESS`).

## 5. Failure policy (current, agreed)

1. Try each preset in the fallback chain.
2. Log each attempt: `START …` / `FAILED with {preset} after {s}: {error}`.
3. If all fail → `status="failed_all_fallbacks"`, write `.stats.json`, checkpoint `result.json`, **skip and continue**.
4. No 1-page retry in default path. 1-page split is an **optional future debug/recovery mode** (see §9).

Observed 66pp run (`177b54cc…`): `pages=66 ok=60 failed=6 | batches=22 ok=20 failed=2`.

## 6. Resume

Key: same bytes → same sha256 → same `data/batches/{sha}/`.

- `_recover_batch_from_artifacts()` requires `batch_{i}.md + .json + .stats.json`, matching `i`/`pages`, resumable `status`, sane numbers.
- Recovered batches are logged as `recovered …` and skipped (no reconversion).
- Incomplete artifacts → `rebuild` with warning. Missing → `pending`.
- Works even if `result.json` is deleted — recovery is artifact-based.
- `resume=True` is default in `run_pdf()` and the `/process` route.

## 7. Storage layout

```text
backend/data/uploads/{sha256}.pdf          # immutable upload copy (dedupe key)
backend/data/batches/{sha256}/
  original.pdf                             # working copy for splitting
  batch_000.pdf / .md / .json / .stats.json
  …
  result.json                              # rolling checkpoint, SQLite-shaped
  merged.md                                # merged text + batch/page-range markers
  merged_manifest.json                     # per-batch stats + doc keys
  merge_result.json                        # validation + output paths
  run.log                                  # full log (console is one-liners)
```

`result.json` shape: `{document, batches[], totals, outputs}` — designed to map into future `coal.db` tables. Never committed (gitignored). Qdrant is untouched in v1.

Merge markers (batch + range only — exact `<!-- page:N -->` needs page-wise artifacts, not yet implemented):

```markdown
<!-- batch:003 pages:10-12 -->
<!-- page-range:10-12 -->
…text…
```

## 8. API (v1, synchronous)

Base: `/api/documents`. Test at `/docs`.

| Method | Route | What |
|---|---|---|
| `POST` | `/upload` | PDF only (rejects non-`.pdf`, empty). Returns `{doc_id, filename, stored_pdf}` |
| `POST` | `/{doc_id}/process` | Runs `run_pdf(preset="scanned", device="auto", resume=True)`. Blocks until done |
| `GET` | `/{doc_id}/result` | Returns saved `result.json`. 404 if never processed |
| `GET` | `/{doc_id}/merged.md` | Downloads `merged.md`. 404 if missing |

Note: `/process` holds the HTTP request open (66pp ≈ 1–3h on CPU). Async jobs are future work.

## 9. Known failures (2026-09-13, 66pp doc)

| Batch | Symptom | Meaning |
|---|---|---|
| `21/22` pp 61-63 | `worker exited with code 3221225477` in all 3 presets, instant | Windows `0xC0000005` access violation — native crash (render/OCR/torch layer), not a Python exception. Subprocess isolation contained it |
| `22/22` pp 64-66 | Earlier: hard timeouts 360s/240s/180s + `MatchingPostProcessor … Orphan pdf_cell` spam. Latest: `exit code 1` after ~117s | `1` = generic child failure with no payload. Old code misreported `0.0s`; runner now measures wall time + returns child traceback when available |

Noisy-but-harmless warnings filtered in `logging_setup.py`: tied-weights, `RTDetrImageProcessor`, HF-hub unauthenticated, `pin_memory`, `torch.quantize_per_tensor` deprecation. Libs (`transformers`, `torch`, `docling`, `easyocr`, `PIL`…) are ERROR-level on console; full detail stays in `run.log`.

## 10. Limits + next steps

Limits:

1. No 1-page retry in default path (by decision).
2. `/process` is synchronous — long PDFs block.
3. Merge has batch/page-range markers, not exact per-page markers.
4. `BATCH_TIMEOUT_S=180` in `config.py` is legacy Docling soft timeout; real control is `TIMEOUTS_S` in runner.
5. Child reloads models per attempt (`Loading weights: 770/770` each fallback) — slow but safe.

Next (pick one):

1. Add `failed_ranges` top-level field to `result.json` for explicit downstream quarantine.
2. Async `/process` (job id + poll) so HTTP doesn't block for hours.
3. Isolated 1-page debug script for pp 61-66 outside the main pipeline.
4. Wire `result.json` batches into PostgreSQL `documents/pages/chunks` via the RAG indexer (`docs/05_RAG_PIPELINE.md`).
