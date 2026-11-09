# 02 — Requirements (SIH26023)

> Status: DRAFT — scope decisions still open. Organized by PS modules + cross-cutting concerns.
> The **Prototype** column now reflects what the code actually does (verified against `backend/app/`),
> not an aspiration: `Done` / `Partial` / `No`. `v2` and `Out` remain TBD.

## M1 — Automated Report Generation Platform

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| M1.1 | Generate parliamentary / administrative inquiry reply with citations | Objectives + Outcome 1 | Done — `parliamentary_reply` template, `reports/pipeline.py`, citation footnotes | TBD | — |
| M1.2 | Generate geological + mining + production figures summary | Objectives + Outcome 1 | Done — `geological_summary` template | TBD | — |
| M1.3 | Embed fact tables + charts in reports | Outcome 1 (figures reporting) | Partial — fact tables yes; charts emit a text *specification*, no chart image | TBD | — |
| M1.4 | Export editable deliverable (DOCX) | Outcome 1 (reporting) | Done — `reports/exporter.py`, approved reports only | TBD | — |

## M2 — Word Cloud + Topic Identification Module

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| M2.1 | Dynamic word cloud from corpus | Outcome 2 | No — `app/analytics/` is an empty package | TBD | — |
| M2.2 | Topic identification from corpus | Outcome 2 | No | TBD | — |
| M2.3 | Corpus-level analytics from single ingestion | Outcome 2 + Benefits | No | TBD | — |

## M3 — AI-Based Query and Response System

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| M3.1 | Grounded answers with text + tables + charts + citations | Outcome 3 + Objectives | Partial — cited answer + validated claims; no tables/charts in the answer | TBD | — |
| M3.2 | Refuse when no reliable evidence (no invented numbers) | Benefits (accuracy) | Done — validator `UNSUPPORTED` path + 404 "No reliable evidence found" | TBD | — |
| M3.3 | Cross-document / comparative questions (year / mine / metric) | Objectives (historical + contemporary) | Partial — `document_id` filter + entity/metric/period filters; no explicit comparison logic | TBD | — |
| M3.4 | Fast response to high-priority inquiries | Benefits | Partial — facts-first path is fast; semantic fallback pays a first-call model load | TBD | — |

## IN — Inputs (cross-cutting, feed M1–M3)

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| IN.1 | Scanned PDFs → text + tables with page provenance | Inputs core | Done — Docling `scanned` preset + PyMuPDF emergency fallback; provenance is page-range | TBD | — |
| IN.2 | Digital PDFs → same downstream | Inputs | Done — text-layer auto-detect upgrades the start preset to `digital` | TBD | — |
| IN.3 | Spreadsheets (XLSX/XLS/CSV) → facts | Inputs | Partial — parsed to Markdown tables + JSON AST and indexed; fact normalization is generic table heuristics | TBD | — |
| IN.4 | Images → OCR path | Inputs | Done — `image_runner.py` wraps the image into a 1-page PDF | TBD | — |
| IN.5 | Historical archives (multi-year corpus) | Inputs | Partial — per-doc batch dirs + `index-all-job` bulk indexing; no dedicated archive/corpus model | TBD | — |

## TR — Trust layer (cross-cutting, M1 + M3)

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| TR.1 | Every number → doc → page → evidence (citations) | Objectives (traceability) | Partial — chunk/fact provenance + claim citations, at page-range granularity | TBD | — |
| TR.2 | Mechanical validation: SUPPORTED / NEEDS_REVIEW / UNSUPPORTED (code, not AI) | Objectives (validation, consistency) | Done — `app/common/validator.py` (QA) + `app/reports/validate.py` (reports) | TBD | — |
| TR.3 | Review workflow: approve / edit / reject per claim + report sign-off | Outcomes (phases: testing, integration) | Done — `app/review/service.py`, `POST /{id}/approve`, `/feedback`, `/review` | TBD | — |

## NF — Non-functional

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| NF.1 | Phased delivery (analysis → digitize → build → test → integrate → train → enhance) | Desired Outcomes | Done — docs 00–10 + ADR log track the phases | TBD | — |
| NF.2 | Time-saved % quantified | Benefits | Partial — `eval.evaluate_time_saved()` exists; no recorded manual baseline run | TBD | — |
| NF.3 | Accuracy % quantified (extraction + generation) | Benefits | Partial — `eval.evaluate_facts()` + `tests/golden_set.json`; not yet a stabilised score | TBD | — |
| NF.4 | Automation % quantified | Benefits | Partial — `eval.evaluate_automation()` exists; no recorded run | TBD | — |
| NF.5 | Scalable foundation (batch + resume; large docs don't kill job) | Objectives (scalable foundation) | Partial — parallel batch workers, hard per-batch timeouts, artifact-based resume; `/process` is still synchronous | TBD | — |

## OS — Explicitly out / roadmap (proposals, not locked)

| ID | Item | Reason |
|----|------|--------|
| OS.1 | Knowledge graph | Not in PS; PostgreSQL facts + provenance suffice (proposal) |
| OS.2 | Model fine-tuning / custom NER | Not in PS (proposal) |
| OS.3 | Auth / RBAC / multi-user | Future ops, not demo (proposal) |
| OS.4 | Full CIL workflow integration + training | Demo handoff only (proposal) |
| OS.5 | Deep archive system | Simplified corpus instead (proposal) |
