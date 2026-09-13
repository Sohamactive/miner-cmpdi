# 03 — Architecture

> Status: DRAFT — nothing locked. Covers: shape, backend modules, stores, report flow, tooling (uv). Frontend detail, contracts, ingestion internals later.
> Built so far: `backend/` skeleton + `docling` dep only. No module code yet.

## 1. Shape: client-server modular monolith
- React frontend (UI) + FastAPI backend (one process, one deploy).
- Frontend↔backend over HTTP job APIs: upload → process → ask → generate → review → export.
- Microservices (split backend) rejected for prototype: one team, one pipeline, one demo laptop.
- Reuses SOW skeleton: staged pipeline + shared state + async jobs + exporter pattern. SOW data never reused.

## 2. Backend modules (decided)
| Module | Owns |
|---|---|
| `api/` | Thin HTTP routing only, no logic |
| `ingestion/` | Upload, type-detect, Docling batches + progress, page markers → raw pages |
| `extraction/` | Chunks + typed facts `{entity, metric, period, value, unit, page, evidence}` in SQLite |
| `knowledge/` | Embeddings + BM25, hybrid retrieve; Qdrant payload mirror |
| `qa/` | Understand → fact-lookup-first → RAG fill → cited answer + refusal |
| `analytics/` | TF-IDF/NMF topics, wordcloud, timeseries (M2) |
| `reports/` | Templates → draft → code-validate → assemble → DOCX (producer) |
| `review/` | Approve/edit/reject + status (judge, separate from reports) |
| `common/` | config, db, llm_client, schemas (shared plumbing) |

No `rag/` folder: memory half in `knowledge/`, mouth half in `qa/`.

## 3. Data stores (decided)
- SQLite `backend/data/coal.db` via `common/db.py`: documents, pages, chunks (authoritative text), facts, claims, reports, reviews, jobs. Never committed.
- Storage paths: SQLite + upload scratch → `backend/data/`. Qdrant disk files → repo-root `qdrant_storage/` (compose mount `./qdrant_storage:/qdrant/storage`) or Docker volume — never inside `backend/data/`.
- Qdrant is a brand-new database for this project: new collection (e.g. `miner_chunks`), fresh empty storage. SOW's `knowledge_base` collection untouched. Same server process may host it; split to a second instance only on port conflicts.
- Chunk text + `{chunk_id, document_id, page, year, mine, section}` stored as Qdrant payload mirror for fast hits; SQLite stays source of truth for citations, validation, eval, export. Rebuild index from SQLite on loss.
- BM25 rebuilt in memory at startup.

## 4. Report flow (proposal)
Select → gather (facts-first, then RAG) → draft per slot → extract claims → mechanical validate (code, not LLM) → assemble (tables/charts/footnotes) → review → DOCX.

## 5. Tooling: uv (decided)
- `backend/` is the uv project root (`pyproject.toml` + `uv.lock` committed); `uv sync` installs; run from `backend/` via `uv run uvicorn app.main:app`.
- Python ≥3.12. Backend and frontend separate roots (`pyproject` vs `package.json`). Frontend not scaffolded yet.
- Installed: `docling` only. Next: FastAPI/uvicorn + ingestion deps when ingestion module starts.

## 6. Open (not decided)
- Embeddings provider (local vs Gemini API).
- Frontend pages/components.
- Ingestion internals beyond the current prototype.

## 7. Current ingestion prototype (open, but implemented)
- PDF-only v1 under `ingestion/`: sha256 fingerprinted upload copy, 3-page batch split, Docling conversion, per-batch artifacts (`.md/.json/.stats.json`), merged markdown, and rolling `result.json` checkpoints.
- Resume policy: same PDF → same sha256 → recover completed batches from per-batch artifacts even if `result.json` is missing, then continue only pending/rebuild batches.
- Failure policy: each batch attempts `scanned` → `light_table` → `ocr_only` under hard per-batch timeouts. If all fallbacks fail, mark that batch `failed_all_fallbacks`, skip it, and continue the document. Prototype priority is forward progress over exhaustive rescue.
- Current output contract: preserve successful pages/batches, quarantine failed batches in stats, and continue downstream with partial ingestion when needed.
- Optional future optimization, not default logic: re-split a failed 3-page batch into 1-page retries for finer salvage. Keep this as a targeted debug/recovery mode because it increases ingestion time and complexity.
