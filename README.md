# M.I.N.E.R.
### Mining Intelligence, Knowledge & Evidence Reporter

SIH project: turn legacy scanned mining PDFs (CMPDI/CIL reports) + digital docs + spreadsheets
into cited parliamentary replies, compliance summaries, and analytics.

> Status: ingestion prototype and retrieval foundation implemented. Docs 00–03 remain DRAFT; 04 and 05 describe implemented pipelines.
> Backend: `app/ingestion/` + `app/api/documents.py` + `app/main.py` exist. See `docs/04_INGESTION_PIPELINE.md`.

[![Open in ToDiagram](https://todiagram.com/images/open-in-todiagram.svg)](https://todiagram.com/editor?doc=212a515fe30b1decff0ba0b1)

<img src="docs/flowchart.svg" alt="flowchart">

## What exists till now

- `docs/00_PROJECT_CONTEXT.md`, `01_PROBLEM_STATEMENT.md`, `02_REQUIREMENTS.md`, `03_ARCHITECTURE.md` (all DRAFT) + `04_INGESTION_PIPELINE.md` (implemented prototype)
- `docs/_archive/` — old scattered drafts, background only
- `backend/` — uv project (`miner-backend`, Python ≥3.12) with Docling ingestion, FastEmbed/Qdrant semantic retrieval, and PostgreSQL evidence storage; `backend/data/` holds runtime ingestion artifacts (gitignored)
- `AGENTS.md` / `CLAUDE.md` — agent operating protocol
- Notion SIH page — Unified Docs Tracker (mirrors local docs)

## Setup (for a new teammate)

```powershell
cd backend
uv sync
uv run uvicorn app.main:app --reload
# open http://localhost:8000/docs
```

Create `backend/.env` from `.env.example` before indexing. Required: `DATABASE_URL`, `QDRANT_URL`, `QDRANT_COLLECTION`, `EMBEDDING_MODEL`. Backend loads `backend/.env` at startup.

PostgreSQL is structured source of truth; Qdrant is rebuildable semantic index.

Recommended local Qdrant (dedicated instance for MINER, avoids conflicts with other projects):

```powershell
docker run -d --name miner-qdrant -p 6334:6333 -v "${PWD}\qdrant_storage_miner:/qdrant/storage" qdrant/qdrant:v1.19.0
# then set QDRANT_URL=http://localhost:6334
```

Indexing is not automatic after ingestion. Use endpoints:

- `POST /api/documents/{doc_id}/index` (sync)
- `POST /api/documents/{doc_id}/index-job` + `GET /api/documents/index-job/{job_id}` (async)
- `POST /api/documents/index-all-job` (index everything with `merged.md` + `result.json`)

## What to do next

1. Read `docs/00_PROJECT_CONTEXT.md` → `01` → `02` → `03` → `04` (in order). PS wins conflicts.
2. Read `docs/05_RAG_PIPELINE.md` for indexing and retrieval commands.
3. Read `docs/10_OPERATIONS_RUNBOOK.md` for day-to-day ingest/index/QA operations.
3. Check the Notion SIH tracker for doc progress before creating new docs.
4. Tooling: `uv` only (`uv sync`, `uv run …`). Never commit `backend/data/coal.db`, model caches, or `qdrant_storage/`.

## Key decisions so far (all OPEN, none locked)

- Docling-leaning ingestion (optimal batch/timeout method still under experiment)
- FastAPI monolith + React, PostgreSQL source of truth + new Qdrant collection (`miner_chunks`) as rebuildable mirror
- Facts-first QA, mechanical (code, not LLM) claim validation
- 1 report template in prototype → 2 final (proposal)
