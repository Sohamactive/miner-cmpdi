# AGENTS.md — Operating Protocol (DRAFT, nothing locked)

## 1. Read first
`docs/00_PROJECT_CONTEXT.md` → `01_PROBLEM_STATEMENT.md` → `02_REQUIREMENTS.md` → `03_ARCHITECTURE.md` → `04_INGESTION_PIPELINE.md`. PS wins conflicts. Check `docs/_archive/` for background only — never treat it as binding. See `README.md` for repo state + setup.

## 2. Current proposals (all open)
- FastAPI monolith + React + PostgreSQL structured evidence store (implemented for RAG) + Qdrant collection (`miner_chunks`) as rebuildable semantic mirror
- Facts-first QA; mechanical (code, not LLM) validation; 1-then-2 report templates
- Ingestion internals: see implemented prototype in `docs/04_INGESTION_PIPELINE.md` (PDF-only v1, skip-after-fallbacks; 1-page retry is optional future)
- None frozen — confirm before building on them.

## 3. What exists (don't rebuild)
- `backend/` uv project (`docling`, `easyocr`, `fastapi[standard]`, `pymupdf`); implemented `backend/app/ingestion/` (config/splitter/converter/pdf_runner/pdf_merge/logging) + `backend/app/api/documents.py` + `backend/app/main.py`
- Docs 00–03 (DRAFT) + `04_INGESTION_PIPELINE.md` (implemented prototype). Notion SIH tracker mirrors doc progress.

## 4. Boundaries
Backend modules per 03 §2 (`api/ingestion/extraction/knowledge/qa/analytics/reports/review/common/`). Frontend in `frontend/` (not scaffolded yet). Never cross module lines without noting it in your final summary.

## 5. Workflow per task
1. Inspect (read/grep) relevant modules + docs before writing.
2. Smallest complete change; every number keeps `{doc, page, evidence}`.
3. Verify by execution (run the script/test); never claim done unverified.
4. Final summary must state: files changed, how verified, open questions, next steps.
5. Architecture changes → propose ADR entry for `09_DECISIONS_LOG.md`; never silently treat proposals as final.

## 6. Tooling
uv only (`uv sync`, `uv run …` from `backend/`). Never pip-install without noting it. Runtime artifacts under `backend/data/`, model caches, and Qdrant storage folders (e.g. `qdrant_storage/`, `qdrant_storage_miner/`) are never committed (see `.gitignore`).

## 7. Storage
`backend/data/` holds runtime ingestion artifacts and scratch only (uploads, batch artifacts, logs).

PostgreSQL is source of truth for structured evidence (documents/chunks/facts/raw Docling JSONB).

Qdrant is rebuildable semantic mirror (collection `miner_chunks`). Run a dedicated Qdrant instance for MINER (separate port/storage) to avoid conflicts with other projects; see `docs/10_OPERATIONS_RUNBOOK.md`.

Indexing is a separate step after ingestion. Use endpoints:

- `POST /api/documents/{doc_id}/index` (sync)
- `POST /api/documents/{doc_id}/index-job` + `GET /api/documents/index-job/{job_id}` (async)
- `POST /api/documents/index-all-job` (bulk async for ready batch dirs)

## 8. Blocked?
Stop, state blocker + what you need, suggest owner — don't guess across it.
