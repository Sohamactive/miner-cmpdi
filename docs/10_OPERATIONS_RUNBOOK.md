# 10 — Operations Runbook (Ingest → Index → QA)

## Goal

Run full loop:

1. Upload document
2. Ingest to artifacts (`merged.md` + `result.json`)
3. Index to PostgreSQL + Qdrant
4. Ask QA

## Start Services

1. Start PostgreSQL container (example name used in this workspace): `docker start bigset-db-1`
2. Start MINER Qdrant container: `docker start miner-qdrant`

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
