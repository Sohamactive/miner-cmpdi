# 02 — Requirements (SIH26023)

> Status: DRAFT — nothing locked. Organized by PS modules + cross-cutting concerns. Scope columns (Prototype / v2 / Out) are TBD — next discussion.

## M1 — Automated Report Generation Platform

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| M1.1 | Generate parliamentary / administrative inquiry reply with citations | Objectives + Outcome 1 | TBD | TBD | — |
| M1.2 | Generate geological + mining + production figures summary | Objectives + Outcome 1 | TBD | TBD | — |
| M1.3 | Embed fact tables + charts in reports | Outcome 1 (figures reporting) | TBD | TBD | — |
| M1.4 | Export editable deliverable (DOCX) | Outcome 1 (reporting) | TBD | TBD | — |

## M2 — Word Cloud + Topic Identification Module

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| M2.1 | Dynamic word cloud from corpus | Outcome 2 | TBD | TBD | — |
| M2.2 | Topic identification from corpus | Outcome 2 | TBD | TBD | — |
| M2.3 | Corpus-level analytics from single ingestion | Outcome 2 + Benefits | TBD | TBD | — |

## M3 — AI-Based Query and Response System

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| M3.1 | Grounded answers with text + tables + charts + citations | Outcome 3 + Objectives | TBD | TBD | — |
| M3.2 | Refuse when no reliable evidence (no invented numbers) | Benefits (accuracy) | TBD | TBD | — |
| M3.3 | Cross-document / comparative questions (year / mine / metric) | Objectives (historical + contemporary) | TBD | TBD | — |
| M3.4 | Fast response to high-priority inquiries | Benefits | TBD | TBD | — |

## IN — Inputs (cross-cutting, feed M1–M3)

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| IN.1 | Scanned PDFs → text + tables with page provenance | Inputs core | TBD | TBD | — |
| IN.2 | Digital PDFs → same downstream | Inputs | TBD | TBD | — |
| IN.3 | Spreadsheets (XLSX) → facts | Inputs | TBD | TBD | — |
| IN.4 | Images → OCR path | Inputs | TBD | TBD | — |
| IN.5 | Historical archives (multi-year corpus) | Inputs | TBD | TBD | — |

## TR — Trust layer (cross-cutting, M1 + M3)

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| TR.1 | Every number → doc → page → evidence (citations) | Objectives (traceability) | TBD | TBD | — |
| TR.2 | Mechanical validation: SUPPORTED / NEEDS_REVIEW / UNSUPPORTED (code, not AI) | Objectives (validation, consistency) | TBD | TBD | — |
| TR.3 | Review workflow: approve / edit / reject per claim + report sign-off | Outcomes (phases: testing, integration) | TBD | TBD | — |

## NF — Non-functional

| ID | Requirement | PS source | Prototype | v2 | Out |
|----|-------------|-----------|-----------|----|-----|
| NF.1 | Phased delivery (analysis → digitize → build → test → integrate → train → enhance) | Desired Outcomes | TBD | TBD | — |
| NF.2 | Time-saved % quantified | Benefits | TBD | TBD | — |
| NF.3 | Accuracy % quantified (extraction + generation) | Benefits | TBD | TBD | — |
| NF.4 | Automation % quantified | Benefits | TBD | TBD | — |
| NF.5 | Scalable foundation (batch + resume; large docs don't kill job) | Objectives (scalable foundation) | TBD | TBD | — |

## OS — Explicitly out / roadmap (proposals, not locked)

| ID | Item | Reason |
|----|------|--------|
| OS.1 | Knowledge graph | Not in PS; SQLite + facts suffice (proposal) |
| OS.2 | Model fine-tuning / custom NER | Not in PS (proposal) |
| OS.3 | Auth / RBAC / multi-user | Future ops, not demo (proposal) |
| OS.4 | Full CIL workflow integration + training | Demo handoff only (proposal) |
| OS.5 | Deep archive system | Simplified corpus instead (proposal) |
