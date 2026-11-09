# M.I.N.E.R. — Mining Intelligence, Knowledge & Evidence Reporter

A prototype that ingests scanned mining reports and produces **cited, evidence-linked report
drafts** (DOCX) for CMPDI/CIL style inquiries.

Its core rule is simple: **AI drafts, code validates.** Every number in a draft must carry
`{document, page, evidence}`. Anything that cannot be traced to a source page is quarantined
and never exported, and when there is no supporting evidence the system refuses instead of
guessing.

The codebase started as a response to problem statement **SIH26023**, but it is written as a
normal, self-contained application.

## Status

Working: ingestion, indexing, retrieval, report generation with claim validation, review
sign-off, and DOCX export.

Not built yet:

- **Word cloud / topic analytics** — `backend/app/analytics/` is an empty package.
- **Rendered charts** — report templates declare chart slots, but only a chart *specification*
  is written into the document. No chart images are produced yet.
- **QA user interface** — `POST /api/qa/ask` works, but the frontend does not expose it. The
  frontend is deliberately minimal: two screens only.

## How it fits together

```
upload  →  ingest (Docling OCR + tables, PyMuPDF fallback, resumable batches)
        →  PostgreSQL    structured evidence: documents / pages / chunks / facts / raw Docling JSONB
        →  Qdrant         semantic mirror of chunks (rebuildable from PostgreSQL)

question  →  retrieve from structured evidence + semantic mirror
          →  draft report sections
          →  mechanical claim validation (SUPPORTED / NEEDS_REVIEW / UNSUPPORTED)
          →  human review and approval
          →  DOCX export (approved, supported content only)
```

PostgreSQL is the source of truth for facts. Qdrant is a rebuildable index for semantic search
and is never authoritative for numbers.

## What works today

| Area | Details |
|---|---|
| Ingestion | PDF, XLSX/XLS/CSV, PNG/JPG/TIFF/BMP/WebP. Docling for OCR and table reconstruction, PyMuPDF emergency fallback, parallel page batches, artifact-based resume. |
| Indexing | Chunking + local FastEmbed embeddings (`BAAI/bge-small-en-v1.5`, 384-dim) into Qdrant collection `miner_chunks`. Sync and async job endpoints. |
| QA | `POST /api/qa/ask` returns a cited answer plus validated claims. Backend only. |
| Reports | Two templates: `parliamentary_reply` and `geological_summary`. Async job API with progress and agent logs. |
| Validation | Mechanical, code-driven checks on every claim. Not an LLM judgement. |
| Review | Approve a report, then export it to DOCX. |
| Frontend | Two screens: **Ingestion Dashboard** and **Report Synthesis**. React 19 + Vite + TypeScript, Tailwind v4. No mock data. |

## Limitations

- `POST /api/documents/{id}/process` is synchronous and CPU-bound: a 66-page scan can take
  1–3 hours. Ingest your corpus ahead of time; indexing is a separate step by design.
- Database tables are created during ingestion. On a brand-new database the report endpoints
  return an error until you have ingested and indexed at least one document.
- No authentication or multi-tenancy.
- Report chart slots currently emit a text specification, not an image.

## Tech stack

| Layer | Choice |
|---|---|
| Ingestion | Docling (EasyOCR, table modes) + PyMuPDF fallback |
| Backend | FastAPI, modular monolith, managed with `uv` |
| Structured store | PostgreSQL (SQLAlchemy + psycopg, JSONB) |
| Semantic index | Qdrant + FastEmbed `bge-small-en-v1.5` |
| LLM | Gemini 2.5 Flash or AWS Bedrock (provider-agnostic client), drafting only |
| Reports | python-docx |
| Frontend | React 19, Vite, TypeScript, Tailwind v4, React Router |

## Run it

Prerequisites: `uv`, Node 18+, Docker.

**1. Services.** Run dedicated instances so they do not clash with other PostgreSQL/Qdrant
containers you may already have:

```powershell
docker run -d --name miner-postgres `
  -e POSTGRES_USER=bigset -e POSTGRES_PASSWORD=bigset -e POSTGRES_DB=miner_db `
  -p 5432:5432 postgres:16

docker run -d --name miner-qdrant `
  -p 6334:6333 -v "${PWD}\qdrant_storage_miner:/qdrant/storage" `
  qdrant/qdrant:v1.19.0
```

Both containers stop when Docker or the machine restarts. Bring them back with:

```powershell
docker start miner-postgres miner-qdrant
```

**2. Backend environment.** The canonical configuration is the repository-root `.env`.
The backend and maintenance scripts load it automatically. Keep credentials out of source
control and rotate any previously exposed keys.

```powershell
Copy-Item .\.env.example .\.env   # then set your database, vector-store, and LLM values
```

**3. Backend** → http://localhost:8000/docs

```powershell
cd backend; uv sync; uv run uvicorn app.main:app --reload
```

**4. Frontend** (new terminal) → http://localhost:5173

```powershell
cd frontend; npm install; npm run dev
```

End-to-end via Swagger (`/docs`): `POST /api/documents/upload` →
`POST /api/documents/{id}/process` → `POST /api/documents/{id}/index-job` (poll
`GET /api/documents/index-job/{job_id}`) → `POST /api/qa/ask` →
`POST /api/reports/generate-job` (poll `GET /api/reports/job/{job_id}`) → approve →
download DOCX.

Operations guide: [`docs/10_OPERATIONS_RUNBOOK.md`](docs/10_OPERATIONS_RUNBOOK.md).

## API

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/documents/upload` | Upload a file, returns `{doc_id}` |
| `POST` | `/api/documents/{id}/process` | Run ingestion (synchronous) |
| `GET` | `/api/documents/{id}/result`, `/merged.md` | Checkpoint JSON / merged markdown |
| `GET` | `/api/documents/uploads`, `/batches` | Inventory and index-readiness flags |
| `POST` | `/api/documents/{id}/index`, `/index-job` | Index into PostgreSQL + Qdrant (sync / async) |
| `GET` | `/api/documents/index-job/{job_id}` | Poll an index job |
| `POST` | `/api/documents/index-all-job` | Bulk async index of ready directories |
| `POST` | `/api/qa/ask` | Cited answer with validated claims |
| `POST` | `/api/reports/generate`, `/generate-job` | Generate a report (sync / async) |
| `GET` | `/api/reports/job/{job_id}` | Poll a report job |
| `GET` | `/api/reports/{id}`, `/claims` | Report JSON and claim flags |
| `GET` | `/api/reports/{id}/state` | Versioned agent state for a report |
| `POST` | `/api/reports/{id}/review` | Structured review comments → revision tasks |
| `POST` | `/api/reports/{id}/feedback` | Human-in-the-loop redraft |
| `POST` | `/api/reports/{id}/approve` | Sign off a report |
| `GET` | `/api/reports/{id}/download.docx` | Export the approved report |

Configuration lives in the root `.env` (see `.env.example`): `DATABASE_URL`, `QDRANT_URL`,
`QDRANT_COLLECTION`, `EMBEDDING_MODEL`, `LLM_PROVIDER` (`gemini`, `bedrock`, or
`bedrock_mantle`), provider keys, `LLM_TIMEOUT_MS`, `EXPORT_FOLDER`, and the Mantle
OpenAI-compatible settings (`MANTLE_BASE_URL`, `MANTLE_API_KEY`, `MANTLE_MODEL`).

## Repo map

```
backend/     FastAPI app (Python 3.12+)
             app/api          HTTP routes
             app/ingestion    file intake, OCR, table extraction
             app/extraction   PostgreSQL models and session setup
             app/knowledge    chunking, embeddings, Qdrant store, retrieval
             app/qa           question answering
             app/reports      pipeline, templates, validation, DOCX export
             app/review       approval service and reviewer-side QA
             app/analytics    (empty — not implemented)
frontend/    React app — Ingestion Dashboard and Report Synthesis
docs/        00 context → 01 problem statement → 02 requirements → 03 architecture
             04 ingestion → 05 RAG → 06 report generation → 09 decisions → 10 runbook
```

## Working on the code

- Read `docs/00` → `01` → `02` → `03` → `04` before changing things. The problem statement
  wins any conflict with other docs.
- Stay inside the backend module boundaries listed above.
- Use `uv` only.
- Verify by running the code, not by inspection.
- Every number keeps `{doc, page, evidence}`.
- Architecture changes get an entry in `docs/09_DECISIONS_LOG.md`.

See [`AGENTS.md`](AGENTS.md) for the full protocol.
