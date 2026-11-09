# 00 — Project Context (2-min read)

## What
M.I.N.E.R. (Mining Intelligence, Knowledge & Evidence Reporter): automated platform that turns legacy scanned mining PDFs + digital docs + spreadsheets + standalone images into cited parliamentary replies, compliance summaries, and analytics.

## Why
CMPDI/CIL analysts manually hunt through scanned annual reports and tables to compile numbers. Slow (days), error-prone (hand-copied figures), untraceable (no source/page link). Judges catch a hallucinated production figure instantly.

## Who
- Users: CMPDI/CIL analysts, Ministry of Coal respondents.
- Builders: SIH team, multi-agent parallel (A–F).
- Evaluators: judges + eval harness (golden facts / questions; see `06` §7.2 and `backend/app/reports/eval.py`).

## Core problem (one line)
Convert table-heavy legacy scans into a structured, provably-sourced fact layer that drafts and mechanically validates evidence-grounded reports.

## Scope now (what actually exists — see `README.md` for the live repo state)

- **Ingestion**: multi-modal via `run_ingest` (`backend/app/ingestion/dispatcher.py`) — PDF, XLSX/XLS/CSV, PNG/JPG/JPEG/TIFF/BMP/WebP. Docling OCR + TableFormer primary, PyMuPDF emergency fallback, parallel batch workers, artifact-based resume. Details: `04_INGESTION_PIPELINE.md`.
- **Storage**: PostgreSQL is the source of truth for structured evidence (documents/pages/chunks/facts/raw Docling JSONB). Qdrant (`miner_chunks`) is a rebuildable semantic mirror. No SQLite. ADR: `09_DECISIONS_LOG.md`.
- **QA / RAG**: facts-first (PostgreSQL) then semantic fallback (Qdrant), mechanically validated (code, not LLM). Details: `05_RAG_PIPELINE.md`.
- **Reports**: exactly 2 templates (`parliamentary_reply`, `geological_summary`), multi-agent drafting over an agent-owned state, mechanical claim validation, HITL revision, DOCX export. Details: `06_REPORT_GENERATION_PIPELINE.md`.
- **Frontend**: React 19 + Vite + TypeScript + Tailwind v4, two screens (Ingestion Dashboard, Report Synthesis).
- **Not built**: word-cloud / topic analytics (`backend/app/analytics/` is an empty package) and rendered chart *images* (templates emit a chart *specification* only).
- Timeline: extended multi-day (not 36h). Old drafts in `docs/_archive/`.

## How to use these docs
Read 00→01→02→03→04 before coding. `01_PROBLEM_STATEMENT.md` wins any conflict. `04`/`05`/`06` are the source of truth for their pipelines. Architecture changes go through an ADR in `09_DECISIONS_LOG.md`.
