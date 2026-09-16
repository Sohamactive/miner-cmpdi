# 09 — Decisions Log

## 2026-09-14 — PostgreSQL for RAG structured evidence

The RAG foundation uses PostgreSQL instead of the earlier open SQLite proposal for normalized facts, provenance, and preserved Docling JSONB. Mining/reporting queries require relational exact filtering and integrity across document, page-range, chunk, and fact records. Qdrant remains a rebuildable semantic mirror and is not authoritative for numerical facts.

This decision applies to the implemented RAG foundation in `docs/05_RAG_PIPELINE.md`; broader application persistence and the draft architecture remain open for team review.
