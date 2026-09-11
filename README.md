# M.I.N.E.R.
### Mining Intelligence, Knowledge & Evidence Reporter

SIH project: turn legacy scanned mining PDFs (CMPDI/CIL reports) + digital docs + spreadsheets
into cited parliamentary replies, compliance summaries, and analytics.

> Status: early scaffold. Docs 00–03 exist (DRAFT, nothing locked).
> Backend skeleton exists. Only dependency so far: `docling`. No module code yet.

[![Open in ToDiagram](https://todiagram.com/images/open-in-todiagram.svg)](https://todiagram.com/editor?doc=212a515fe30b1decff0ba0b1)

<img src="docs/flowchart.svg" alt="flowchart">

## What exists till now

- `docs/00_PROJECT_CONTEXT.md`, `01_PROBLEM_STATEMENT.md`, `02_REQUIREMENTS.md`, `03_ARCHITECTURE.md` (all DRAFT)
- `docs/_archive/` — old scattered drafts, background only
- `backend/` — uv project (`miner-backend`, Python ≥3.12) with `docling` added; empty module skeleton under `backend/app/` (`api/common/ingestion/extraction/knowledge/qa/analytics/reports/review/`); `backend/data/` holds runtime DB/scratch (gitignored)
- `AGENTS.md` / `CLAUDE.md` — agent operating protocol
- Notion SIH page — Unified Docs Tracker (mirrors local docs)

## Setup (for a new teammate)

```powershell
cd backend
uv sync
```

No API keys, no Docker, no Qdrant needed yet. Model weights download on first Docling run.

## What to do next

1. Read `docs/00_PROJECT_CONTEXT.md` → `01` → `02` → `03` (in order). PS wins conflicts.
2. Next work item: `backend/app/ingestion/` + `api` for ingestion (plan in chat; not started).
3. Check the Notion SIH tracker for doc progress before creating new docs.
4. Tooling: `uv` only (`uv sync`, `uv run …`). Never commit `backend/data/coal.db`, model caches, or `qdrant_storage/`.

## Key decisions so far (all OPEN, none locked)

- Docling-leaning ingestion (optimal batch/timeout method still under experiment)
- FastAPI monolith + React, SQLite source of truth + new Qdrant collection (`miner_chunks`) as rebuildable mirror
- Facts-first QA, mechanical (code, not LLM) claim validation
- 1 report template in prototype → 2 final (proposal)
