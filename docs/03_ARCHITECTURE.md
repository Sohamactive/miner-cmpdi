# 03 — Architecture

> Status: DRAFT. Ingestion (`04`), retrieval (`05`) and report generation (`06`) are implemented as described below. Frontend pages exist (two screens); analytics (M2) and rendered chart images remain open.

## 1. Shape: client-server modular monolith
- React frontend (UI) + FastAPI backend (one process, one deploy).
- Frontend↔backend over HTTP job APIs: upload → process → ask → generate → review → export.
- Microservices (split backend) rejected for prototype: one team, one pipeline, one demo laptop.
- Reuses SOW skeleton: staged pipeline + shared state + async jobs + exporter pattern. SOW data never reused.

## 2. Backend modules (decided)
| Module | Owns |
|---|---|
| `api/` | Thin HTTP routing only, no logic |
| `ingestion/` | Upload, type-detect, Docling batches + progress, page markers → raw pages |
| `extraction/` | SQLAlchemy models + session + conservative table→fact normalization. Owns `documents`, `pages`, `chunks`, `facts`, `raw_docling_documents`, plus the report tables `reports`, `claims`, `review_decisions`, `report_jobs` |
| `knowledge/` | Chunking, FastEmbed embeddings, Qdrant store, semantic retrieval. No BM25 implemented — retrieval is semantic-only |
| `qa/` | Empty package. The implemented QA responder lives in `app/review/qa/` (see note below) |
| `analytics/` | Empty package — TF-IDF/NMF topics, wordcloud, timeseries (M2) not built |
| `reports/` | Templates → evidence → per-section agents → code-validate → assemble → DOCX. Also `state.py` (agent-owned `ReportState`), `agents/`, `eval.py` |
| `review/` | Approve/edit/reject + status (judge, separate from reports); hosts the QA responder in `review/qa/` |
| `common/` | `llm_client.py` (provider-agnostic LLM) + `validator.py` (mechanical claim validator). No shared `db`/`schemas` module yet |

No `rag/` folder: memory half in `knowledge/`, mouth half in `qa/`.

Module-line note: the QA responder physically sits in `review/qa/` (imported by `api/qa.py`) rather than in `qa/`, which is still empty. Moving it to `qa/` is a pending cleanup; until then this crosses the `qa`/`review` line.

## 3. Data stores
- PostgreSQL via SQLAlchemy/psycopg: documents, pages, chunks, facts, raw Docling JSONB, and the report/claim/review tables. PostgreSQL is authoritative for structured facts and provenance.
- Storage paths: runtime ingestion artifacts + upload scratch → `backend/data/` (`uploads/`, `batches/`, `reports/`). Qdrant disk files → repo-root `qdrant_storage_miner/` (mounted into the dedicated container) — never inside `backend/data/`.
- Qdrant is a brand-new database for this project: new collection (`miner_chunks`), fresh empty storage. SOW's `knowledge_base` collection untouched. Run it as a dedicated instance (host port `6334`) to avoid clashing with other projects.
- Qdrant payload per point: `{chunk_id, document_id, filename, page_range, batch, section, text}`. PostgreSQL stays source of truth for citations, validation, eval, and export. Rebuild the index from PostgreSQL/artifacts on loss.
- No BM25 and no in-memory lexical index: retrieval is embedding-based (`SemanticRetriever`) plus exact fact filtering in PostgreSQL.

## 4. Report flow (implemented, see `06`)
Select template → gather evidence (facts-first in PostgreSQL, then semantic in Qdrant) → per-section drafting agents writing one owned `ReportState` path → extract claims → mechanical validation (code, not LLM) → assemble (fact tables, chart specs, citation footnotes) → HITL feedback/review → approve → DOCX (supported claims only).

## 5. Tooling: uv (decided)
- `backend/` is the uv project root (`pyproject.toml`); `uv sync` resolves and installs. Run from `backend/` via `uv run uvicorn app.main:app --reload`.
- `uv.lock` is **not currently committed** — `uv sync` regenerates it locally. Committing it is open work (it should be, for reproducible installs).
- Python ≥3.12 (dev machine observed on 3.13). Backend and frontend are separate roots (`pyproject.toml` vs `package.json`).
- Declared backend dependencies: `fastapi[standard]`, `docling`, `easyocr`, `pymupdf`, `sqlalchemy`, `psycopg[binary]`, `qdrant-client`, `fastembed`, `python-docx`, `matplotlib`, `boto3`/`botocore`, `google-genai`.
  Note: `matplotlib` and `google-genai` are declared but charts are not yet rendered and Gemini is reached via `google-genai` only when `LLM_PROVIDER=gemini`.

## 6. Open (not decided)
- Analytics module (M2) — `analytics/` is empty.
- Rendered chart images (templates emit specs only).
- Committing `uv.lock`; moving the QA responder out of `review/qa/`.
- Ingestion internals beyond the current prototype (`04` §10).

## 7. Current ingestion prototype (open, but implemented)
- Multi-modal under `ingestion/`: sha256 fingerprinted upload copy; PDFs split into 3-page batches, spreadsheets parsed sheet-by-sheet, images wrapped into a 1-page PDF; Docling conversion in a parallel worker pool; per-batch artifacts (`.md/.json/.stats.json`), merged markdown, and rolling `result.json` checkpoints.
- Resume policy: same bytes → same sha256 → recover completed batches from per-batch artifacts even if `result.json` is missing, then continue only pending/rebuild batches.
- Failure policy: each batch attempts `scanned` → `light_table` → `ocr_only` under hard per-batch timeouts, then a native PyMuPDF salvage pass. If everything fails, mark that batch `failed_all_fallbacks`, skip it, and continue the document. Prototype priority is forward progress over exhaustive rescue.
- Current output contract: preserve successful pages/batches, quarantine failed batches in stats, and continue downstream with partial ingestion when needed.
- Optional future optimization, not default logic: re-split a failed 3-page batch into 1-page retries for finer salvage. Keep this as a targeted debug/recovery mode because it increases ingestion time and complexity.
