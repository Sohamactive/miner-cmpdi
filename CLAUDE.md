# CLAUDE.md — Operating Protocol (DRAFT, nothing locked)

## 1. Read first
`docs/00_PROJECT_CONTEXT.md` → `01_PROBLEM_STATEMENT.md` → `02_REQUIREMENTS.md` → `03_ARCHITECTURE.md` → `04_INGESTION_PIPELINE.md` → `05_RAG_PIPELINE.md` → `06_REPORT_GENERATION_PIPELINE.md`. PS wins conflicts. Check `docs/_archive/` for background only — never treat it as binding. See `README.md` for repo state + setup.

## 2. Current proposals (all open)
- PostgreSQL structured evidence store (implemented for RAG) + Qdrant collection (`miner_chunks`) as a rebuildable semantic mirror — no SQLite.
- Facts-first QA; mechanical (code, not LLM) validation; 2 report templates (`parliamentary_reply`, `geological_summary`).
- Ingestion is multi-modal (PDF/XLSX/XLS/CSV/images) with PyMuPDF emergency fallback; internals in `docs/04_INGESTION_PIPELINE.md`.
- Not built: analytics module (`app/analytics/` empty), rendered chart images.
- None frozen — confirm before building on them.

## 3. What exists (don't rebuild)
- `backend/` uv project (`docling`, `easyocr`, `fastapi[standard]`, `pymupdf`, `sqlalchemy`, `psycopg[binary]`, `qdrant-client`, `fastembed`, `python-docx`, `matplotlib`, `boto3`, `google-genai`).
- Implemented: `backend/app/ingestion/`, `extraction/`, `knowledge/`, `reports/` (+ `reports/agents/`), `review/` (+ `review/qa/`), `common/llm_client.py`, `common/validator.py`, `api/{documents,reports,qa}.py`, `main.py`.
- `frontend/` React 19 + Vite + TS + Tailwind v4, two screens (Ingestion Dashboard, Report Synthesis).
- Docs 00–06, 09, 10 (DRAFT). Notion SIH tracker mirrors doc progress.

## 4. Boundaries
Backend modules per 03 §2 (`api/ingestion/extraction/knowledge/qa/analytics/reports/review/common/`). Known deviations: the QA responder lives in `review/qa/` while `qa/` is empty. Never cross module lines without noting it in your final summary.

## 5. Workflow per task
1. Inspect (read/grep) relevant modules + docs before writing.
2. Smallest complete change; every number keeps `{doc, page, evidence}`.
3. Verify by execution (run the script/test); never claim done unverified.
4. Final summary must state: files changed, how verified, open questions, next steps.
5. Architecture changes → propose ADR entry for `09_DECISIONS_LOG.md`; never silently treat proposals as final.

## 6. Tooling
uv only (`uv sync`, `uv run …` from `backend/`). Never pip-install without noting it. `uv.lock` is not committed yet. `backend/data/` (uploads, batches, reports), model caches, and Qdrant storage folders (e.g. `qdrant_storage_miner/`) are never committed (see `.gitignore`).

## 7. Storage
`backend/data/` holds runtime ingestion artifacts and scratch only (uploads, batch artifacts, logs, exports). PostgreSQL is the source of truth for structured evidence (documents/pages/chunks/facts/raw Docling JSONB + reports/claims/review tables). Qdrant is a rebuildable semantic mirror (collection `miner_chunks`); run a dedicated instance for MINER (separate port/storage).

## 8. Blocked?
Stop, state blocker + what you need, suggest owner — don't guess across it.
