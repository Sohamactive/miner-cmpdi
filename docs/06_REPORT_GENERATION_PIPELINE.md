# 06 — Report Generation Pipeline

> Status: BUILDING (Phase 0). Follows `05_RAG_PIPELINE.md`. Source of truth for `backend/app/reports/`.

## 1. What it does (30 sec)

Turns evidence (numbers from PostgreSQL + story from Qdrant) into cited, machine-validated reports you can correct until you like them.

* Default: fixed Parliamentary Reply template (no choices needed).
* Custom: you say what sections you want, agent follows your spec.
* Human-in-loop: draft v1 → your feedback → v2 → ... → approve → DOCX download.
* Every number must have proof: `{document, page_range, evidence}`. No proof = quarantine, never exported.

## 2. Data flow

```
User spec: {question, template | custom_sections, doc_ids[]}
        |
  [Phase 1 — Retriever]
  LLM generates 3-4 search queries
  + search_facts(entity, metric, period)  (PostgreSQL)
  + SemanticRetriever.search(query)        (Qdrant)
        |                                  |
  facts[]                              chunks[]
        |                                  |
  EvidenceBundle { facts, chunks, coverage_warnings }
        |
  [Phase 2 — Writer + Validator + Assembler]
  LLM draft per section from bundle
  -> code validate (SUPPORTED / NEEDS_REVIEW / UNSUPPORTED)
  -> assemble: fact tables, matplotlib charts, citation footnotes
        |
  [Phase 3 — HITL Loop]
  Draft v1 -> user feedback -> v2 -> ... -> approved
  -> python-docx export (cover, headings, TOC, tables, charts, citations)
        |
  Async job: queued -> running -> needs_review -> approved -> exported
```

## 3. Phase 0 — Contracts + plumbing (no logic yet)

### 3.1 New files

| File | Owns |
|------|------|
| `app/common/llm_client.py` | Provider-agnostic LLM, JSON mode, retry/backoff, extractive fallback |
| `app/reports/schemas.py` | Pydantic models: `ReportSpec`, `GeneratedReport`, `Claim`, `ReviewDecision` |
| `app/reports/templates.py` | Template registry: section list + slots + style |

### 3.2 DB tables (extend `extraction/models.py`)

```
reports:     id, report_type, status, title, parameters_json, sections_json,
             version, parent_id, created_at, updated_at

claims:      id, report_id, claim_text, fact_id, document_id, page_range,
             evidence_text, value, unit, validation_status, validation_reasons,
             confidence, created_at

review_decisions: id, report_id, claim_id, action (APPROVE/EDIT/REJECT),
                  reviewer_note, edited_text, created_at

report_jobs: id, job_type, status (queued/running/needs_review/approved/exported),
             step_index, step_label, progress, error, result_json,
             created_at, updated_at
```

### 3.3 Template registry

* `parliamentary_reply` (default, fixed): sections = `[preamble, facts_summary, evidence_table, analysis, conclusion, citations]`
* `geological_summary`: sections = `[overview, geological_data, production_figures, charts, recommendations]`
* Custom user spec: `custom_sections[]` overrides template section list; unknown slots rejected with `400`.

### 3.4 Dependencies (no new pip installs)

All from existing `pyproject.toml`: `fastapi`, `sqlalchemy`, `qdrant-client`, `fastembed`.
New optional deps for charts/export: `python-docx`, `matplotlib` (to add in Phase 3).

## 4. Phase 1 — Hybrid evidence retriever

### 4.1 New file

`app/reports/retrieval.py`

### 4.2 Flow

1. Parse `ReportSpec` → extract topic keywords.
2. LLM generates 3-4 search queries (port SOW `retrieval_agent.py:29-52`).
3. Parallel: `search_facts(entity, metric, period)` from PostgreSQL + `SemanticRetriever.search(query)` from Qdrant.
4. Dedupe by `chunk_id` / `evidence` text.
5. Attach provenance: `{document_id, page_range, evidence_text}` to every item.
6. Exclude failed/timeout batches (per `indexer.py:41-43`).
7. Return `EvidenceBundle{facts[], chunks[], coverage_warnings[]}`.

### 4.3 No LLM drafting here

This phase only gathers evidence. Writing is Phase 2.

## 5. Phase 2 — Writer + validator + assembler

### 5.1 New files

| File | Owns |
|------|------|
| `app/reports/writer.py` | LLM drafts sections from bundle + template |
| `app/reports/validate.py` | Code checks: value-in-evidence, unit/period/entity match, citation present |
| `app/reports/assembler.py` | Fact tables, matplotlib charts (PNG in-memory), citation footnotes |

### 5.2 Writer (`writer.py`)

* Prompt = template sections + EvidenceBundle + custom_sections (if any).
* Output JSON: `{sections[{heading, paragraphs, fact_ids, chart_spec}]}`.
* Truncate input like SOW `MAX_PIPELINE_INPUT_CHARS` (30000 chars).
* Port SOW `proposal_agent.py:38-49` pattern.

### 5.3 Validator (`validate.py`) — code, not LLM

Per `01_PROBLEM_STATEMENT.md:48`:
* `SUPPORTED`: value present in evidence text, unit matches, period matches, citation present.
* `NEEDS_REVIEW`: partial match (value present but unit/period unclear).
* `UNSUPPORTED`: value not in evidence, no citation. Quarantined, never exported.

### 5.4 Assembler (`assembler.py`)

* Fact tables from `facts[]` via `python-docx`.
* Charts via `matplotlib` (production by year/mine/metric) → PNG in-memory → embed.
* Citation footnotes: `[{doc, page, evidence}]` per claim.
* Graceful skip when data absent (per `_archive/initals_2.md:17`).

## 6. Phase 3 — HITL loop + jobs + DOCX

### 6.1 New files

| File | Owns |
|------|------|
| `app/reports/pipeline.py` | Orchestrator: gather → draft → validate → assemble → HITL loop |
| `app/reports/exporter.py` | DOCX export: cover, headings, TOC, tables, charts, footnotes |
| `app/api/reports.py` | Thin HTTP routes (port SOW `routes.py:246-326` pattern) |
| `app/review/` | Approve/edit/reject per claim + report sign-off (separate module per `03:21`) |

### 6.2 Pipeline (`pipeline.py`)

Port SOW `pipeline.py:31-94`:
1. `gather` (Phase 1 retriever)
2. `draft` (Phase 2 writer)
3. `validate` (Phase 2 validator)
4. `assemble` (Phase 2 assembler)
5. Auto-review: if any `UNSUPPORTED`, flag `needs_review`.
6. Single auto-retry if review fails (SOW pattern).

### 6.3 HITL loop

* `POST /api/reports/{id}/feedback {note, edited_sections}` → re-run writer with `reviewer_feedback` appended (SOW `proposal_agent.py:43-46`), re-validate, version `v1, v2, ...`.
* Cap: 5 iterations + 600s timeout (SOW defaults).
* `POST /api/reports/{id}/approve` → sign-off → DOCX export ready.

### 6.4 DOCX exporter (`exporter.py`)

Port SOW `proposal_exporter.py:18-57`:
* `python-docx` with cover page, headings, TOC, fact tables, embedded chart PNGs, citation footnotes.
* Only `SUPPORTED + approved NEEDS_REVIEW` claims exported.
* `UNSUPPORTED` quarantined in review table.

### 6.5 API routes (`api/reports.py`)

Thin HTTP only (per `03:12`), port SOW async job pattern:

| Method | Route | What |
|--------|-------|------|
| `POST` | `/api/reports/generate-job` | Start async generation → `{job_id}` |
| `GET` | `/api/reports/job/{job_id}` | Poll: step/progress/status |
| `GET` | `/api/reports/{id}` | Get report JSON |
| `GET` | `/api/reports/{id}/claims` | Get claim list with validation status |
| `POST` | `/api/reports/{id}/feedback` | User feedback → re-draft |
| `POST` | `/api/reports/{id}/approve` | Sign-off → export ready |
| `GET` | `/api/reports/{id}/download.docx` | Download DOCX |

## 7. Phase 4 — Frontend + metrics

### 7.1 UI

* Template dropdown (default Parliamentary Reply) + custom sections textarea.
* Status poll: `queued → running → needs_review → approved → exported`.
* Claim table with `SUPPORTED/NEEDS_REVIEW/UNSUPPORTED` flags.
* Feedback text box for HITL.
* Approve button → download DOCX.

### 7.2 Eval metrics (per `01:55-59`)

* Time saved: `(manual - AI) / manual` on one reply draft.
* Accuracy: golden 20 facts matched on `value+unit+period` + correct citation.
* Automation: `automated steps / total steps`.
* Method: golden set + `eval.py` on every run.

## 8. File map (new files only)

```text
backend/app/
  common/llm_client.py          LLM provider, JSON mode, retry/backoff
  reports/
    __init__.py
    schemas.py                  Pydantic models
    templates.py                Template/style registry
    retrieval.py                Hybrid evidence gatherer (Phase 1)
    writer.py                   LLM section drafter (Phase 2)
    validate.py                 Mechanical claim validation (Phase 2)
    assembler.py                Tables, charts, footnotes (Phase 2)
    pipeline.py                 Orchestrator + HITL loop (Phase 3)
    exporter.py                 DOCX export (Phase 3)
  review/
    __init__.py
    models.py                   Review decision models
  api/reports.py                Thin HTTP routes (Phase 3)
```

## 9. Open questions

1. **LLM provider**: Gemini (SOW default) vs Groq Llama 3.3 70B? Recommend provider-agnostic with Gemini default.
2. **Default template**: `parliamentary_reply` — confirmed?
3. **HITL cap**: 5 iterations + 600s timeout — confirmed?
4. **ADR needed**: PostgreSQL vs SQLite conflict in `AGENTS.md` vs implemented.
