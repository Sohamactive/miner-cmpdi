# 09 — Decisions Log

## 2026-09-14 — PostgreSQL for RAG structured evidence

The RAG foundation uses PostgreSQL instead of the earlier open SQLite proposal for normalized facts, provenance, and preserved Docling JSONB. Mining/reporting queries require relational exact filtering and integrity across document, page-range, chunk, and fact records. Qdrant remains a rebuildable semantic mirror and is not authoritative for numerical facts.

This decision applies to the implemented RAG foundation in `docs/05_RAG_PIPELINE.md`; broader application persistence and the draft architecture remain open for team review.

## 2026-09-16 — Dedicated Qdrant Instance for MINER (Operational Safety)

Run a dedicated Qdrant instance for MINER (separate port/storage) to avoid conflicts with other local projects and to keep MINER's semantic index rebuildable. If a Qdrant instance becomes unhealthy/corrupt, MINER can rebuild the `miner_chunks` collection from PostgreSQL/chunk artifacts without impacting other collections.

Pin Qdrant server version close to `qdrant-client` version to avoid compatibility issues.
