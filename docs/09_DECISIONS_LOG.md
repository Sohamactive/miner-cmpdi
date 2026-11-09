# 09 — Decisions Log

## 2026-09-14 — PostgreSQL for RAG structured evidence

The RAG foundation uses PostgreSQL instead of the earlier open SQLite proposal for normalized facts, provenance, and preserved Docling JSONB. Mining/reporting queries require relational exact filtering and integrity across document, page-range, chunk, and fact records. Qdrant remains a rebuildable semantic mirror and is not authoritative for numerical facts.

This decision applies to the implemented RAG foundation in `docs/05_RAG_PIPELINE.md`; broader application persistence and the draft architecture remain open for team review.

## 2026-09-16 — Dedicated Qdrant Instance for MINER (Operational Safety)

Run a dedicated Qdrant instance for MINER (separate port/storage) to avoid conflicts with other local projects and to keep MINER's semantic index rebuildable. If a Qdrant instance becomes unhealthy/corrupt, MINER can rebuild the `miner_chunks` collection from PostgreSQL/chunk artifacts without impacting other collections.

Pin Qdrant server version close to `qdrant-client` version to avoid compatibility issues.

## 2026-09-16 — Multi-modal ingestion with a PyMuPDF emergency fallback

Ingestion accepts PDF, XLSX/XLS/CSV, and standalone images through one entrypoint (`ingestion/dispatcher.run_ingest`), normalising every input to the same artifact contract (`result.json` + per-batch `.md/.json/.stats.json` + `merged.md`). Docling remains the primary extractor; when every Docling preset fails on a batch (native crash such as Windows `0xC0000005`, or a hard timeout), a native PyMuPDF pass recovers text and tables and records `status="partial_fallback_pymupdf"`. Rationale: the prototype must never lose a page to a single crashed library, and forward progress matters more than exhaustive rescue.

## 2026-09-16 — Parallel batch workers with subprocess isolation and hard timeouts

PDF batches run in a `ThreadPoolExecutor` (`MAX_WORKERS`, default 2) instead of strictly sequentially, while each batch attempt executes in its own `spawn` subprocess with a per-preset hard kill (`TIMEOUTS_S`). Rationale: a 66-page scan took 1–3 hours on CPU; parallel batches cut wall time without letting a native crash or a hung OCR run take down the orchestrator. Consequence: RAM scales with worker count, so `MAX_WORKERS` must be raised only with headroom.

## 2026-09-16 — Report generation as agents over one single-writer state

Report drafting is modelled as agents (`EvidenceAgent`, per-section `SectionAgent`, `ValidationAgent`, `TestingAgent`, `ReviewAgent`) that share a single `ReportState` and may write only the paths they own (`state.apply_agent_update` rejects cross-agent writes). Section agents may run in parallel, but results are merged only after all workers finish, keeping the state single-writer. Rationale: parallel drafting without a lost-update or cross-write bug, plus an auditable `change_log` and per-agent `agent_logs` for the UI.

## 2026-10-19 — Documentation resynchronised to the implemented code

Docs 00–06 previously described an earlier proposal (Docling-only ingestion, SQLite, Streamlit, no frontend, empty module skeleton). They now describe what `backend/app/` and `frontend/` actually do, including two known deviations that are not yet fixed in code: the QA responder sits in `review/qa/` while `app/qa/` is still empty, and `app/analytics/` remains an empty package. `uv.lock` is not committed.
