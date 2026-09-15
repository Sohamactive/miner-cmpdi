# 00 — Project Context (2-min read)

## What
M.I.N.E.R. (Mining Intelligence, Knowledge & Evidence Reporter): automated platform that turns legacy scanned mining PDFs + digital docs + spreadsheets into cited parliamentary replies, compliance summaries, and analytics.

## Why
CMPDI/CIL analysts manually hunt through scanned annual reports and tables to compile numbers. Slow (days), error-prone (hand-copied figures), untraceable (no source/page link). Judges catch a hallucinated production figure instantly.

## Who
- Users: CMPDI/CIL analysts, Ministry of Coal respondents.
- Builders: SIH team, multi-agent parallel (A–F).
- Evaluators: judges + eval harness (golden 20 facts / 20 questions).

## Core problem (one line)
Convert table-heavy legacy scans into a structured, provably-sourced fact layer that drafts and mechanically validates evidence-grounded reports.

## Scope now
- Docling-only ingestion (canonical). Optimal method still open — see `13_DOCLING_RUNBOOK.md`.
- Exactly 2 report templates. TF-IDF+NMF analytics (no BERTopic). SQLite monolith (FastAPI + Streamlit).
- Timeline: extended multi-day (not 36h). Old drafts in `docs/_archive/`.


## How to use these docs
Read 00→01→02→03→04 before coding. Contracts in 06/07 are binding for parallel agents. Changes go through ADR in 09.
