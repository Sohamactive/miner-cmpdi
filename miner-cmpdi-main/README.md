# M.I.N.E.R.
### Mining Intelligence, Knowledge & Evidence Reporter

SIH project: turn legacy scanned mining PDFs (CMPDI/CIL reports) + digital docs + spreadsheets
into cited parliamentary replies, compliance summaries, and analytics.

> Status: ingestion prototype implemented (PDF-only v1, unstable on hard pages). Docs 00–03 DRAFT + 04 implemented.
> Backend: `app/ingestion/` + `app/api/documents.py` + `app/main.py` exist. See `docs/04_INGESTION_PIPELINE.md`.

[![Open in ToDiagram](https://todiagram.com/images/open-in-todiagram.svg)](https://todiagram.com/editor?doc=212a515fe30b1decff0ba0b1)

<img src="docs/flowchart.svg" alt="flowchart">

## What exists till now

- `docs/00_PROJECT_CONTEXT.md`, `01_PROBLEM_STATEMENT.md`, `02_REQUIREMENTS.md`, `03_ARCHITECTURE.md` (all DRAFT) + `04_INGESTION_PIPELINE.md` (implemented prototype)
- `docs/_archive/` — old scattered drafts, background only
- `backend/` — uv project (`miner-backend`, Python ≥3.12) with `docling`, `easyocr`, `fastapi[standard]`, `pymupdf`; implemented `app/ingestion/` (config/splitter/converter/pdf_runner/pdf_merge/logging) + `app/api/documents.py` + `app/main.py`; `backend/data/` holds runtime DB/scratch (gitignored)
- `AGENTS.md` / `CLAUDE.md` — agent operating protocol
- Notion SIH page — Unified Docs Tracker (mirrors local docs)

## Setup (for a new teammate)

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
# open http://localhost:8000/docs
```

No API keys, no Docker, no Qdrant needed yet. Model weights download on first Docling run.

## What to do next

1. Read `docs/00_PROJECT_CONTEXT.md` → `01` → `02` → `03` → `04` (in order). PS wins conflicts.
2. Next work item: you own the rewrite — `04_INGESTION_PIPELINE.md` §10 lists options (failed_ranges, async jobs, SQLite wiring).
3. Check the Notion SIH tracker for doc progress before creating new docs.
4. Tooling: `uv` only (`uv sync`, `uv run …`). Never commit `backend/data/coal.db`, model caches, or `qdrant_storage/`.

## Key decisions so far (all OPEN, none locked)

- Docling-leaning ingestion (optimal batch/timeout method still under experiment)
- FastAPI monolith + React, SQLite source of truth + new Qdrant collection (`miner_chunks`) as rebuildable mirror
- Facts-first QA, mechanical (code, not LLM) claim validation
- 1 report template in prototype → 2 final (proposal)
