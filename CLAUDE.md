# CLAUDE.md — Operating Protocol (DRAFT, nothing locked)

## 1. Read first
`docs/00_PROJECT_CONTEXT.md` → `01_PROBLEM_STATEMENT.md` → `02_REQUIREMENTS.md` → `03_ARCHITECTURE.md`. PS wins conflicts. Check `docs/_archive/` for background only — never treat it as binding. See `README.md` for repo state + setup.

## 2. Current proposals (all open)
- Docling-leaning ingestion (optimal method still under experiment — see chat/Kaggle findings)
- FastAPI monolith + React + SQLite source of truth + new Qdrant collection (`miner_chunks`)
- Facts-first QA; mechanical (code, not LLM) validation; 1-then-2 report templates
- None frozen — confirm before building on them.

## 3. What exists (don't rebuild)
- `backend/` uv project with `docling` installed; empty module skeleton under `backend/app/` (all `__init__.py` + `data/.gitkeep`)
- Docs 00–03 (DRAFT). Notion SIH tracker mirrors doc progress.

## 4. Boundaries
Backend modules per 03 §2 (`api/ingestion/extraction/knowledge/qa/analytics/reports/review/common/`). Frontend in `frontend/` (not scaffolded yet). Never cross module lines without noting it in your final summary.

## 5. Workflow per task
1. Inspect (read/grep) relevant modules + docs before writing.
2. Smallest complete change; every number keeps `{doc, page, evidence}`.
3. Verify by execution (run the script/test); never claim done unverified.
4. Final summary must state: files changed, how verified, open questions, next steps.
5. Architecture changes → propose ADR entry for `09_DECISIONS_LOG.md`; never silently treat proposals as final.

## 6. Tooling
uv only (`uv sync`, `uv run …` from `backend/`). Never pip-install without noting it. `backend/data/coal.db`, model caches, `qdrant_storage/` never committed (see `.gitignore`).

## 7. Storage
`backend/data/` holds SQLite + scratch only. Qdrant is a new collection (`miner_chunks`) with disk files at root `qdrant_storage/` or a volume — never inside `backend/data/`. SQLite is source of truth; Qdrant payload is a rebuildable mirror.

## 8. Blocked?
Stop, state blocker + what you need, suggest owner — don't guess across it.

do it good