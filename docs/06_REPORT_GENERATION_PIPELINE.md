# 06 — Report Generation Pipeline

> Status: IMPLEMENTED (all phases landed). Remaining gaps: chart *images* are not rendered, per-claim review UI is backend-only, and eval golden lists are placeholders.
> Follows `05_RAG_PIPELINE.md`. Source of truth for `backend/app/reports/`.

## 1. What it does (30 sec)

Turns evidence (numbers from PostgreSQL + story from Qdrant) into cited, machine-validated reports you can correct until you like them.

* Default: fixed Parliamentary Reply template (no choices needed).
* Custom: you may pass `custom_sections` (validated against the template's slots).
* Human-in-loop: draft v1 → feedback/review → v2 → ... → approve → DOCX download.
* Every number must have proof: `{document, page_range, evidence}`. No proof = quarantine, never exported.
* Charts: the writer may emit a `chart_spec`; the assembler and exporter pass a **textual specification** through. No PNG/image is produced yet (`matplotlib` is a declared dependency but unused).

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
  per-section agents draft from bundle
  -> code validate (SUPPORTED / NEEDS_REVIEW / UNSUPPORTED)
  -> assemble: fact tables, chart specifications, citation footnotes
        |
  [Phase 3 — HITL Loop]
  Draft v1 -> user feedback -> v2 -> ... -> approved
  -> python-docx export (cover, headings, TOC, tables, charts, citations)
        |
  Async job: queued -> running -> needs_review -> approved -> exported
```

## 3. Contracts + plumbing

### 3.1 Files

| File | Owns |
|------|------|
| `app/common/llm_client.py` | Provider-agnostic LLM (`gemini` \| `bedrock`), JSON mode, retry/backoff with `retry in Ns` parsing, `generate_json` / `generate_json_or_none` |
| `app/reports/schemas.py` | Pydantic models: `ReportSpec`, `GeneratedReport`, `Claim`, `ReportSection`, `EvidenceBundle`, `ReviewDecision`, `ReportJobStatus` |
| `app/reports/templates.py` | Template registry: section list + slots + style, `validate_custom_sections()` |
| `app/reports/state.py` | `ReportState` (agent-owned, versioned) + `apply_agent_update()` which rejects cross-agent writes |

### 3.2 DB tables (in `extraction/models.py`)

```
reports:     id, report_type, status, title, parameters_json (holds question + report_state),
             sections_json, version, parent_id, created_at, updated_at

claims:      id, report_id, claim_text, fact_id, document_id, page_range,
             evidence_text, value, unit, validation_status, validation_reasons,
             confidence, created_at

review_decisions: id, report_id, claim_id, action (APPROVE/EDIT/REJECT),
                  reviewer_note, edited_text, created_at

report_jobs: id, job_id, report_id, status (queued/running/needs_review/approved/exported),
             step_index, step_label, progress, error, result_json,
             created_at, updated_at
```

Note: `report_jobs` is declared but the running app tracks jobs in an in-memory dict in `api/reports.py`; the table is not written yet.

### 3.3 Template registry (`templates.py`)

* `parliamentary_reply` (default): `[preamble, facts_summary, evidence_table, production_chart, analysis, conclusion, citations]`
* `geological_summary`: `[overview, geological_data, production_figures, trend_chart, recommendations, citations]`
* Custom user spec: `custom_sections[]` overrides the template's section list; names outside the template's slots are rejected (`ValueError` → 400-class behaviour).

### 3.4 Dependencies

All installed per `backend/pyproject.toml`: `fastapi[standard]`, `sqlalchemy`, `psycopg[binary]`, `qdrant-client`, `fastembed`, `python-docx`, `matplotlib`, `google-genai`, `boto3`/`botocore`.

## 4. Hybrid evidence retriever

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

## 5. Writer + validator + assembler

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

* Fact tables from validated claims (`build_fact_table`) — `SUPPORTED` + `NEEDS_REVIEW` rows only, `UNSUPPORTED` skipped.
* Chart handling: `build_chart_placeholder()` returns the section's `chart_spec` unchanged (production by year/mine/metric is intended, but **no matplotlib PNG is generated yet**).
* Citation footnotes: `[{doc, page, evidence}]` per claim via `build_citations()`.
* Section `evidence_table`, `production_figures`, and `facts_summary` get the fact table; empty tables are omitted.

## 6. HITL loop + jobs + DOCX

### 6.1 Files

| File | Owns |
|------|------|
| `app/reports/pipeline.py` | `ReportPipeline`: run → gather → draft → validate → assemble → persist; `revise()` for the HITL loop |
| `app/reports/agents/report_agents.py` | `EvidenceAgent`, `SectionAgent`, `SpecializedDraftAgent` (parallel section workers), `ValidationAgent`, `TestingAgent`, `ReviewAgent`, plus an unused `DraftAgent` |
| `app/reports/state.py` | Agent-owned `ReportState` with per-agent write ownership and a `change_log` |
| `app/reports/exporter.py` | DOCX export: cover, overview, TOC field, headings, tables, chart note, citations, review summary |
| `app/reports/eval.py` | Golden facts/questions, accuracy / time-saved / automation metrics |
| `app/api/reports.py` | Thin HTTP routes + in-memory job registry |
| `app/review/service.py` | Approve/edit/reject per claim + report sign-off (separate module per `03` §2) |
| `app/review/qa/` | QA responder used by `POST /api/qa/ask` |

### 6.2 Pipeline (`pipeline.py`)

1. `gather` — `EvidenceAgent` → `gather_evidence()` (Phase 1 retriever)
2. `draft` — `SpecializedDraftAgent`: one `SectionAgent` per heading, drafted in a `ThreadPoolExecutor` (`REPORT_AGENT_MAX_WORKERS`, default 3) and merged only after workers finish
3. `validate` — `ValidationAgent` (claims) then `TestingAgent` (section completeness + resolvable `F#`/`C#` references)
4. `assemble` — `assemble_sections()`
5. Persist to PostgreSQL; status is always set to `needs_review`
6. `revise()` — re-drafts targeted sections from `report_state` and reviewer feedback

Progress/agent callbacks drive the async job's step + agent log.

### 6.3 HITL loop

* `POST /api/reports/{id}/feedback {note, edited_sections}` → re-draft (state-aware when `report_state` exists), re-validate, bump `version`.
* Cap: `MAX_REVISIONS = 5`; `REPORT_TIMEOUT_S = 600` is declared but not enforced by a watchdog.
* `POST /api/reports/{id}/review {comments[]}` → `ReviewAgent` turns comments into persisted `revision_tasks`, sets status `revision_requested`.
* `POST /api/reports/{id}/approve` → sign-off → DOCX export ready.

### 6.4 DOCX exporter (`exporter.py`)

* `python-docx` output: header/footer with page field, cover page, "Report Overview" with metadata table, updatable TOC field, one heading per section, claim table for table sections, chart specification note, citations list, review summary.
* Only `SUPPORTED` + `NEEDS_REVIEW` claims are exported; `UNSUPPORTED` is skipped (quarantined).
* Export path: `EXPORT_FOLDER` env (default `data/reports`); file `report-{id}.docx`.
* `export_docx` raises at runtime if `python-docx` is missing.

### 6.5 API routes (`api/reports.py`)

Thin HTTP only (per `03` §2):

| Method | Route | What |
|--------|-------|------|
| `POST` | `/api/reports/generate` | Sync generation, returns the full result |
| `POST` | `/api/reports/generate-job` | Start async generation → `{job_id}` |
| `GET` | `/api/reports/job/{job_id}` | Poll: step/progress/status/agent_logs |
| `GET` | `/api/reports/{id}` | Get report JSON + claims |
| `GET` | `/api/reports/{id}/claims` | Claim list with validation status + reasons |
| `GET` | `/api/reports/{id}/state` | Versioned agent `ReportState` from `parameters_json` |
| `POST` | `/api/reports/{id}/feedback` | User feedback → re-draft |
| `POST` | `/api/reports/{id}/review` | Structured review comments → revision tasks |
| `POST` | `/api/reports/{id}/approve` | Sign-off → export ready |
| `GET` | `/api/reports/{id}/download.docx` | Download DOCX (requires status `approved`/`exported`) |

## 7. Frontend + metrics

### 7.1 UI (as built — `frontend/src/pages/ReportSynthesisPage.tsx`)

* Question textarea, report title input, template dropdown (Parliamentary reply / Geological summary).
* `POST /api/reports/generate-job` then poll `GET /api/reports/job/{job_id}` every 900 ms; 5-step progress track.
* Agent ledger: per-agent status + duration from `agent_logs`.
* Result panel: section/claim/supported counts, then Approve, Download DOCX, or Open JSON.

Not in the UI yet: custom-section editor, per-claim review table with `SUPPORTED/NEEDS_REVIEW/UNSUPPORTED` flags, feedback box, claim-level approve/edit/reject.

### 7.2 Eval metrics (`eval.py`, per `01` §3.3)

* `evaluate_facts()` — golden facts matched on `value` + `unit`; `evaluate_claims()` — support rate.
* `evaluate_time_saved()` — `(manual - ai) / manual`; `evaluate_automation()` — `automated / total`.
* `run_full_evaluation()` logs all four. `GOLDEN_FACTS`/`GOLDEN_QUESTIONS` are placeholder FY2024-25 numbers; `backend/tests/golden_set.json` (1984 ECL/manpower facts) is the ingestion-derived set used by tests. Reconcile before quoting a score.

## 8. File map

```text
backend/app/
  common/
    llm_client.py               LLM provider, JSON mode, retry/backoff
    validator.py                Mechanical claim validator (QA path)
  reports/
    __init__.py
    schemas.py                  Pydantic models
    templates.py                Template/style registry
    state.py                    Agent-owned ReportState
    retrieval.py                Hybrid evidence gatherer (Phase 1)
    writer.py                   LLM section drafter (used by revise path)
    validate.py                 Mechanical claim validation (Phase 2)
    assembler.py                Tables, chart specs, citations (Phase 2)
    pipeline.py                 Orchestrator + HITL loop (Phase 3)
    exporter.py                 DOCX export (Phase 3)
    eval.py                     Golden set + metrics
    agents/
      __init__.py
      report_agents.py          Evidence/Section/Draft/Validation/Testing/Review agents
  review/
    __init__.py
    service.py                  Approve/edit/reject + sign-off
    qa/
      __init__.py
      models.py                 QAClaim / QAResponse
      responder.py              QA responder
  api/reports.py                Thin HTTP routes
  api/qa.py                     Thin HTTP route
```

## 9. Open questions

1. **LLM provider** — resolved in code: provider-agnostic with `gemini` default, `bedrock` supported via `LLM_PROVIDER` (`.env.example` ships `bedrock`).
2. **Default template** — resolved: `parliamentary_reply`.
3. **HITL cap** — `MAX_REVISIONS = 5` implemented; the 600 s timeout is a constant, not an enforced watchdog.
4. **ADR** — resolved: `09_DECISIONS_LOG.md` records PostgreSQL over SQLite.
5. Still open: render chart PNGs, expose per-claim review + feedback in the UI, reconcile the two golden sets, and wire `report_jobs` to the DB instead of the in-memory registry.
