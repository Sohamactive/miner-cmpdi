# 05 — RAG Pipeline

> Status: IMPLEMENTED foundation. Indexing + retrieval implemented; QA responder exists but remains prototype-grade.

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
- `pages`: batch/page-range status records for future page-level expansion.
- `chunks`: authoritative chunk text and provenance.
- `facts`: normalized numeric candidates with evidence and provenance.
- `raw_docling_documents`: one preserved JSONB payload per source batch.

Qdrant collection `miner_chunks` stores semantic vectors and payload fields `chunk_id`, `document_id`, `filename`, `page_range`, `batch`, `section`, and `text`. The default local model is `BAAI/bge-small-en-v1.5` through FastEmbed, dimension 384, cosine distance. `HashEmbeddingProvider` is available only for deterministic tests/dry runs.

## Local setup

```bash
cd backend
uv sync
cp ../.env.example .env  # edit credentials/URLs when needed
docker run -d --name miner-qdrant -p 6334:6333 qdrant/qdrant:v1.19.0
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

QA uses facts-first (PostgreSQL) then semantic fallback (Qdrant).

## Limitations and future work

Implemented now: artifact indexing, provenance-aware chunking, local embedding abstraction, Qdrant semantic search, PostgreSQL raw JSONB storage, and conservative table-to-fact normalization.

Future: LLM answer generation, QA chatbot/router, mechanical claim validation, complete multimodal RAG, XLSM/image/graph retrieval, report generation integration, richer entity/period/unit extraction, and exact page-level markers for flattened Docling Markdown.

## Recent Improvements (Ops)

1. Dedicated MINER Qdrant instance recommended (separate port/storage) to avoid cross-project conflicts and simplify rebuilds.
2. Embedding upsert now supports small batches (`EMBED_BATCH_SIZE`) to reduce RAM spikes on large docs.
