# 05 — RAG Pipeline

> Status: IMPLEMENTED foundation. Indexing + retrieval + QA endpoint implemented; the QA responder is prototype-grade (extractive, no LLM drafting on the fact path).

## Flow

```text
existing ingestion
  merged.md + result.json + batch JSON
       |                         |
       v                         v
 provenance-aware chunks   raw JSONB + conservative facts
       |                         |
 local FastEmbed             PostgreSQL
       v                         |
 Qdrant miner_chunks            |
       \_________________________/
          inspectable evidence
```

The indexer is `app.knowledge.indexer.index_ingestion_artifacts`. It accepts an existing `data/batches/{sha256}` directory and never runs ingestion again. Batches marked `failed`, `failed_all_fallbacks`, or `timeout` are excluded. Successful batch JSON is retained as raw JSONB, and Markdown markers are copied into every chunk.

## Storage

PostgreSQL is used instead of MongoDB because mining facts need exact filtering by entity, metric, period, value, and unit, plus relational provenance. The implemented tables are:

- `documents`: SHA256 document ID, filename, source path, status.
- `pages`: declared for page-level status, but **not yet populated** by the indexer (chunks carry `page_range` instead).
- `chunks`: authoritative chunk text and provenance.
- `facts`: normalized numeric candidates with evidence and provenance. `normalize_table_facts()` returns `(completed, partial)`; completed facts are stored when at least 3 of entity/metric/period/unit were detected, partial rows are stored too (flagged, for manual review).
- `raw_docling_documents`: one preserved JSONB payload per source batch, keyed by a hash of `(document_id, batch, page_range, payload)`.

Report tables (`reports`, `claims`, `review_decisions`, `report_jobs`) live in the same schema — see `06`.

Qdrant collection `miner_chunks` stores semantic vectors and payload fields `chunk_id`, `document_id`, `filename`, `page_range`, `batch`, `section`, and `text`. The default local model is `BAAI/bge-small-en-v1.5` through FastEmbed, dimension 384, cosine distance. `HashEmbeddingProvider` is available only for deterministic tests/dry runs. Qdrant errors are swallowed (logged, empty result) so a broken mirror never breaks the app.

## Local setup

```bash
cd backend
uv sync
cp ../.env.example .env  # edit credentials/URLs when needed
docker run -d --name miner-qdrant -p 6334:6333 \
  -v "${PWD}/../qdrant_storage_miner:/qdrant/storage" qdrant/qdrant:v1.19.0
uv run uvicorn app.main:app --reload
```

Notes:
- Backend loads `backend/.env` automatically.
- Default embed batch size is `EMBED_BATCH_SIZE` (env) or 16. Smaller reduces RAM spikes.

PostgreSQL must already contain `miner_db`; the first schema operation creates only the application tables. Ingestion remains the existing API flow:

```text
POST /api/documents/upload
POST /api/documents/{doc_id}/process
```

Indexing (writes PostgreSQL + Qdrant; does not run ingestion):

```text
POST /api/documents/{doc_id}/index          # sync
POST /api/documents/{doc_id}/index-job      # async, returns job_id
GET  /api/documents/index-job/{job_id}
POST /api/documents/index-all-job           # async, indexes all ready batch dirs
```

Index an existing artifact directory from Python:

```python
from app.knowledge.embeddings import FastEmbedProvider
from app.knowledge.indexer import index_ingestion_artifacts
from app.knowledge.qdrant_store import QdrantStore

index_ingestion_artifacts(
    "data/batches/<sha256>",
    embedder=FastEmbedProvider(),
    qdrant=QdrantStore(),
)
```

Semantic retrieval uses `SemanticRetriever.search(query)` and returns text plus document/page-range provenance. Exact retrieval uses `search_facts(...)` in `app.extraction.postgres`; no LLM is involved in either path.

QA endpoint (prototype):

```text
POST /api/qa/ask
```

QA uses facts-first (PostgreSQL) then semantic fallback (Qdrant) and returns a cited answer plus mechanically validated claims. When nothing is found it returns HTTP 404 with `"No reliable evidence found for this question."` Note: the responder class lives in `app/review/qa/` (imported by `app/api/qa.py`); `app/qa/` is still an empty package (`03` §2 module-line note).

The report pipeline does not reuse the QA responder; it has its own hybrid retriever (`app/reports/retrieval.py`) that gathers an `EvidenceBundle` of facts + chunks — see `06` §4.

## Limitations and future work

Implemented now: artifact indexing, provenance-aware chunking, local embedding abstraction, Qdrant semantic search, PostgreSQL raw JSONB storage, conservative table-to-fact normalization, and dependency-free validator/QA tests.

Future: LLM answer generation for the QA path, a QA chatbot/router, complete multimodal RAG (XLSM/graph retrieval), richer entity/period/unit extraction, and exact page-level markers for flattened Docling Markdown.

## Recent Improvements (Ops)

1. Dedicated MINER Qdrant instance recommended (separate port/storage) to avoid cross-project conflicts and simplify rebuilds.
2. Embedding upsert now supports small batches (`EMBED_BATCH_SIZE`) to reduce RAM spikes on large docs.
