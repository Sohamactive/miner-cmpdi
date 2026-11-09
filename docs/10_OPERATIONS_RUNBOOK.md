# 10 — Operations Runbook (Ingest → Index → QA → Report)

## Goal

Run full loop:

1. Upload document
2. Ingest to artifacts (`merged.md` + `result.json`)
3. Index to PostgreSQL + Qdrant
4. Ask QA
5. Generate → approve → export a report

## Start Services

Dedicated MINER containers (names and credentials as in `README.md` / `.env.example`):

1. Start PostgreSQL: `docker start miner-postgres` (created with user/password/db `bigset`/`bigset`/`miner_db`)
2. Start MINER Qdrant: `docker start miner-qdrant` (host port `6334` → container `6333`)

If a container does not exist yet, see the `docker run` commands in `README.md` ("Run it").

## Start Backend

1. Run from `backend/`: `uv run uvicorn app.main:app --reload`
2. Open Swagger: `http://localhost:8000/docs`

Backend loads `backend/.env` automatically.

## Ingest

1. `POST /api/documents/upload` with file
2. Copy returned `doc_id` (sha256)
3. `POST /api/documents/{doc_id}/process`
4. Wait until `GET /api/documents/{doc_id}/merged.md` returns 200

Ingest output lives under `backend/data/batches/{doc_id}/`.

## Index

Index requires `backend/data/batches/{doc_id}/merged.md` and `result.json`.

1. Sync index: `POST /api/documents/{doc_id}/index`
2. Async index: `POST /api/documents/{doc_id}/index-job` then poll `GET /api/documents/index-job/{job_id}`
3. Bulk async: `POST /api/documents/index-all-job` then poll `GET /api/documents/index-job/{job_id}`

Notes:

1. `job_id` is not `doc_id`. Always poll with returned `job_id`.
2. Use small `embed_batch_size` (example 4 or 8) if RAM limited.
3. Indexing does upsert only. No deletes.

## QA

1. `POST /api/qa/ask` with JSON:
2. Example:
   `{ "question": "growth rate during 1984-85 over 1983-84 (%)", "document_id": "<doc_id>" }`

Common input failure:

1. Trailing comma in JSON causes 422. JSON must not contain trailing commas.
2. With no evidence the endpoint returns 404 `"No reliable evidence found for this question."` — that is the refusal path, not a server error.

## Report

Requires indexed evidence; the report tables are created on first use (same `create_schema`).

1. Sync: `POST /api/reports/generate` with `{ "question": "...", "report_type": "parliamentary_reply", "title": "..." }`
2. Async: `POST /api/reports/generate-job` then poll `GET /api/reports/job/{job_id}`
3. Inspect: `GET /api/reports/{report_id}` and `GET /api/reports/{report_id}/claims`
4. Revise: `POST /api/reports/{report_id}/feedback` (max 5 revisions) or `POST /api/reports/{report_id}/review`
5. Approve: `POST /api/reports/{report_id}/approve`
6. Export: `GET /api/reports/{report_id}/download.docx` (writes `EXPORT_FOLDER`, default `backend/data/reports`)

Notes:

1. Report jobs are held in process memory — a backend restart loses job status for in-flight runs.
2. A report with `UNSUPPORTED` claims still reaches `needs_review`; those claims are quarantined and never exported.

## Troubleshooting

Qdrant errors (500, panics, internal error):

1. Treat semantic index as broken.
2. Start fresh MINER Qdrant on new port/storage.
3. Update `QDRANT_URL` in `backend/.env`.
4. Re-run indexing (Qdrant is rebuildable mirror).

Slow QA:

1. Check PostgreSQL up.
2. First embedding call is slow (model init). Later calls should be fast.

## Stats (Observed In This Workspace)

These numbers are from local runs on this repo state (Windows, CPU).

1. Embedding model reuse: first embed call ~1.136s, next embed call ~0.003s (same process) after adding per-process FastEmbed model cache.
2. Indexing stability: indexing 10 ready batch dirs completed 10/10 successfully after switching to dedicated Qdrant instance and embedding in small batches (`EMBED_BATCH_SIZE=8`).
3. Corpus indexed (example run): PostgreSQL `chunks` = 454, Qdrant `miner_chunks` points = 454 (counts match).
4. QA noise reduction: filtered page-range and year-range junk numbers (examples removed: 1, -3, -84 from `1-3` / `1983-84`).
