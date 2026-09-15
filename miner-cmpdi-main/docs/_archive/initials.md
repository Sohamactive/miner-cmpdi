# SIH26023 — Architecture & Project-Memory Initialization Plan

## 0. Core Problem Analysis

**Real problem:** CMPDI/CIL's parliamentary-inquiry workflow is manual: analysts hunt through legacy scanned PDFs, annual reports, and spreadsheets to compile numbers and narrative; results are slow (days), error-prone (hand-transcribed numbers), and untraceable (no source/page linkage).

**Core engineering problem (one sentence):**
> The real engineering problem is converting a heterogeneous corpus of legacy scanned mining documents — dominated by tables, numbers, and domain vocabulary — into a structured, provably-sourced knowledge layer that can automatically draft and mechanically validate evidence-grounded parliamentary and compliance reports.

**Hardest technical problems (ranked):**
1. **OCR + table reconstruction from legacy scanned PDFs** with page-level provenance (numbers are the payload; degraded scans break naive OCR).
2. **Structured fact extraction** — turning messy text/tables into typed facts `{entity, metric, period, value, unit}` that survive cross-document consistency checks.
3. **Evidence-grounded RAG** — every answer/report claim maps to retrievable evidence (document→page→section), with refusal when evidence is absent.
4. **Report drafting + claim validation with human-in-the-loop** — multi-section documents with citations, mechanically validated numeric claims, and a genuine approve/edit/reject workflow.
5. **Cross-document temporal reasoning** (production by year/mine across reports) — simplified to fact-aggregation queries for MVP.

## 1. Requirements Matrix (ruthless)

| ID | Requirement | Source | Priority | AI? | Demo | Complexity | Decision |
|----|-------------|--------|----------|-----|------|-----------|----------|
| R1 | Extract structured tabular+text from legacy scanned PDFs | PS core | P0 | OCR | High | High | **P0** — PaddleOCR + PP-Structure tables  or docling|
| R2 | RAG chatbot for parliamentary coal inquiries | PS | P0 | Yes | High | Med | **P0** |
| R3 | Automated compliance + geological summary reports with citations | PS | P0 | Yes | High | Med | **P0** — exactly 2 templates |
| R4 | Dynamic word clouds + topic models | PS | P0 | Partial | High | Med | **P0** — TF-IDF + NMF (not BERTopic) |
| R5 | Interactive reviewer interface (human-in-the-loop) | PS | P0 | No | High | Med | **P0** — simplified |
| R6 | Digital PDF / DOCX / XLSX / image ingestion | Background | P0 | No | Med | Med | **P0** — pdfplumber / python-docx / openpyxl |
| R7 | Historical archives | Background | — | — | — | — | **SIMPLIFY** — multi-year corpus (FY21–FY25), not a deep archive system |
| R8 | Cross-document / comparative questions | QA types | P0 | Yes | High | Med | **P0** — via fact aggregation by year/entity |
| R9 | Refuse unanswerable questions | Quality | P0 | Yes | Med | Low | **P0** — evidence-gate + warnings |
| R10–12 | Quantified accuracy %, time-saved %, automation % | Benefits | P1 | No | Med | Med | **P1** — evaluation harness + demo metrics |
| R13 | Knowledge graph | Not in PS | — | — | — | — | **REMOVE** — SQLite + JSON facts suffice |
| R14 | Model fine-tuning / custom NER training | Not in PS | — | — | — | — | **REMOVE** |
| R15 | Auth / RBAC / multi-user | Future | — | — | — | — | **P2 / REMOVE** for MVP (local demo) |
| R16 | Integration with CIL subsidiary workflows | Desired | — | — | — | — | **P2** — demo the handoff point only |
| R17 | Reranking | Not required | — | — | — | — | **REMOVE** (hybrid retrieval is enough at this scale) |
| R18 | Trends / timeline analytics | Analytics | P1 | No | Med | Med | **P1** — plotly line chart from facts |

## 2. The 36-Hour MVP — One Coherent Vertical Slice

```
Scanned legacy PDF + digital PDF + XLSX
  → upload & type-detect (scanned vs digital via text-extraction probe)
  → OCR (scanned) / direct parse (digital)
  → page + section provenance
  → table extraction → deterministic fact extraction
  → normalize → SQLite (facts, pages, chunks)
  → embed + BM25 → hybrid index
  → "parliamentary question" → fact lookup + retrieval → grounded answer + citations
  → generate Parliamentary Reply Draft / Geological Summary
  → mechanical claim validation (SUPPORTED / NEEDS_REVIEW / UNSUPPORTED)
  → reviewer screen (approve / edit / reject) → export DOCX
```

Normalized documents feed **both** the knowledge/RAG path and the analytics path (word cloud, topics, trend charts) — one ingestion, three consumers, so the demo feels like one system.

## 3. Final Architecture — Modular Monolith (FastAPI + Streamlit)

```
┌──────────────┐  HTTP  ┌───────────────────┐
│  Streamlit   │◀──────▶│  FastAPI monolith │
│  frontend    │        │  (uvicorn)        │
└──────────────┘        └────────┬──────────┘
          ┌──────────────────────┼───────────────────────┐
          ▼                      ▼                       ▼
   document intelligence    knowledge layer         analytics
   (ingest/OCR/parse/       (chunk/embed/BM25/      (TF-IDF/NMF,
    table/extract facts)     hybrid retrieval)       wordcloud, trends)
          │                      │                       │
          └──────────┬───────────┴───────────┬───────────┘
                     ▼                       ▼
              qa layer                 reports + review
          (query understanding,     (drafting, claim
           grounded answer,           validation, DOCX
           refusal)                   export, HITL)
                     ▼
            SQLite (single file):
       documents/pages/chunks/facts/claims/reports/reviews
                     + embeddings (BLOB) + BM25 in memory
```

**Modules (backend/app/):**
- `ingestion/` — upload, type detection, processing pipeline, background jobs
- `ocr/` — PaddleOCR primary, Tesseract fallback, image preprocessing
- `parse/` — pdfplumber (digital PDF text+tables), python-docx, openpyxl
- `extraction/` — table→facts, regex→facts, optional LLM assist, provenance assembly
- `knowledge/` — section-aware chunking, local embeddings, numpy vector index, BM25, hybrid fusion, metadata filters (year/mine/document/section)
- `qa/` — query understanding (parse year/entity/metric), routing (facts vs RAG), answer generation, claim extraction, refusal gate
- `analytics/` — TF-IDF corpus stats, NMF topics, word cloud, fact timeseries
- `reports/` — 2 templates, section drafting from facts+evidence, claim validation, DOCX export
- `review/` — review decisions (APPROVE/EDIT/REJECT/FLAG), report status transitions
- `common/` — provider-agnostic LLM client, config, logging, db access
- `api/` — route modules per contract in 07_API_CONTRACTS.md

**Why monolith:** one process, one database, one deploy command; parallel agent work is achieved via module boundaries, not services. **Why FastAPI:** typed Pydantic contracts + auto `/docs` OpenAPI — the frontend agent works purely from the contract. **Why Streamlit:** one Python app builds all screens in hours; no separate build pipeline; Plotly + wordcloud render natively.

## 4. Final Technology Stack (with selection rationale)

| Component | Choice | Why | Alternative (rejected) | Risk / Fallback |
|---|---|---|---|---|
| OCR | **PaddleOCR + PP-Structure** | Best open accuracy on degraded English scans; built-in table→HTML reconstruction; pip-installable | Tesseract (needs system binary, poor tables); Azure Doc AI (needs network+keys) | Heavy install (~1GB). **Fallback:** Tesseract. **Emergency:** pre-extracted text committed in repo |
| Digital PDF | **pdfplumber** | Text + tables + coordinates in one lib → provenance trivially | pypdf (text only) | Low. Fallback: pypdf |
| DOCX / XLSX | **python-docx / openpyxl** | Zero risk, standard | — | None |
| Embeddings | **sentence-transformers all-MiniLM-L6-v2** (local, offline, 384-d) | Free, offline → retrieval works even if LLM API dies; Groq has no embedding API | OpenAI embeddings (needs key); fastembed/ONNX (lighter but less documented) | ~2GB torch install. Fallback: fastembed |
| Vector search | **numpy brute-force cosine in memory** (vectors persisted as BLOB in SQLite) | Zero infra; <100 ms at 5–50k chunks | FAISS (index mgmt code), Chroma/Qdrant/pgvector (extra services) | Fine at corpus scale. Fallback: FAISS |
| Keyword search | **rank_bm25** + hybrid fusion (RRF) | Domain terms ("overburden", "MCL") need lexical match; cheap | — | None |
| LLM | **Groq Llama 3.3 70B** (JSON mode) via thin client | Free key (user-confirmed), fast, strong JSON output | OpenAI/Gemini (no keys) | Rate limits. **Fallback:** OpenAI/Gemini if key appears. **Emergency:** deterministic **extractive answer mode** (facts + top passages, templated, no LLM) — demo survives API death |
| Analytics | **scikit-learn TF-IDF + NMF**; wordcloud lib | Deterministic, explainable, one pipeline feeds both topics and word cloud | BERTopic (heavy, nondeterministic) | Low |
| Database | **SQLite single file** | Zero setup, single process, portable | Postgres+pgvector, sqlite-vec (setup/ops risk) | None at this scale |
| Report export | **DOCX via python-docx** | CIL's real deliverable format; no LibreOffice dependency | PDF export (needs system LibreOffice) | Fallback: HTML/Markdown download; Emergency: on-screen copyable text |
| Frontend | **Streamlit** (5 screens) + Plotly | Fastest path to a polished demo; multi-page app feel | React/Next.js (doubles effort, separate build) | None |
| Backend | **FastAPI + uvicorn**, background jobs table | Typed contracts; long OCR runs as pollable background jobs | Flask (no typed contracts) | None |
| Deployment | **Local** (two commands); docker-compose optional P2 | One demo laptop | Kubernetes etc. (REMOVE) | — |

## 5. Storage Schema (SQLite, single `coal.db`)

- `documents(id, title, filename, file_type, doc_type, source, year, status, stats_json, created_at)`
- `pages(id, document_id, page_number, text, table_html, image_path, ocr_engine, confidence, has_table)`
- `chunks(id, document_id, page_id, section, text, token_count, embedding BLOB)`
- `facts(id, document_id, page_id, section, entity, metric, period, value, unit, evidence_text, extraction_method, confidence, status, created_at)`
- `claims(id, claim_text, fact_id, document_id, page_id, evidence_text, value, unit, report_id, validation_status, validation_reasons, confidence, created_at)`
- `reports(id, report_type, status, title, parameters_json, sections_json, created_at, updated_at)`
- `review_decisions(id, report_id, claim_id, action, reviewer_note, edited_text, created_at)`
- `jobs(id, job_type, status, progress, error, created_at)`

## 6. Shared Data Contracts (defined in 06_DATA_CONTRACTS.md)

```json
// StructuredFact
{ "entity": "MCL", "metric": "coal_production", "period": "FY2024-25",
  "value": 173.6, "unit": "MT", "document_id": "doc_3", "page": 47,
  "section": "Production", "evidence_text": "Raw coal production ... 173.6 MT",
  "extraction_method": "table|regex|llm", "confidence": 0.95 }
```
Also defined: `Document`, `DocumentPage`, `DocumentChunk`, `Evidence`, `Claim`, `Citation`, `QueryResponse` (answer, claims, citations, facts_used, confidence, grounded, mode: RAG/FACTS/EXTRACTIVE/NO_EVIDENCE, warnings), `GeneratedReport` (sections + claim refs), `ReviewDecision`, `Topic`.

**Fact extraction strategy (deterministic-first):** table rows → facts (conf 0.95) → regex over text lines using metric vocabulary (production, overburden, exploration, despatch; mine names + CIL subsidiary aliases; FY patterns; MT/lakh-tonne units) → LLM assist only for flagged ambiguous lines (conf 0.7). **Claim IDs** = deterministic hash of (doc_id, page, evidence, value) for dedupe. **Validation** = mechanical checks (evidence exists, value matches evidence, unit/year/entity match, citation present) → SUPPORTED / NEEDS_REVIEW / UNSUPPORTED; no "LLM guarantees truth" claims anywhere.

## 7. API Contracts (defined in 07_API_CONTRACTS.md — frontend/backend agents must use only this)

- `POST /api/documents/upload` (multipart) → `document_id` · `POST /api/documents/{id}/process` → `job_id` · `GET /api/jobs/{id}` (progress polling)
- `GET /api/documents` · `GET /api/documents/{id}` · `GET /api/documents/{id}/pages` · `GET /api/documents/{id}/facts`
- `GET /api/facts?mine=&metric=&year=` · `POST /api/qa/ask {question}` → `QueryResponse`
- `GET /api/analytics/wordcloud?corpus=` · `GET /api/analytics/topics?k=` · `GET /api/analytics/facts/timeseries?metric=`
- `POST /api/reports/generate {type, params}` → `report_id` · `GET /api/reports/{id}` · `GET /api/reports/{id}/claims` · `POST /api/reports/{id}/export` (DOCX) · `POST /api/reports/{id}/review {decision, edits}`
- Errors: standardized `{error: {code, message}}` JSON; CORS enabled for localhost:8501.

## 8. 36-Hour Plan

| Hours | Milestone |
|---|---|
| 0–2 | Architecture freeze; repo init (git); **all 15 docs scaffolded**; sample corpus generation (synthetic digital PDF + scanned-looking legacy table doc + XLSX + public CIL reports if fetchable); eval golden set (20 facts, 20 questions) |
| 2–8 | **Parallel:** Agent A schema+config+LLM client; Agent B ingestion/OCR/table/facts; Agent C knowledge/retrieval; Agent D analytics; Agent E reports/review scaffolds; Agent F frontend shell from API contract |
| 8–12 | **First vertical slice end-to-end:** upload → facts → ask → cited answer |
| 12–18 | Core functionality: hybrid retrieval, refusal, 2 report templates, claim validation |
| 18–24 | Analytics + review workflow + DOCX export integrated into UI |
| 24–28 | Integration + polish (one coherent demo flow) |
| 28–31 | Evaluation harness runs; results into 10_TESTING_EVALUATION.md |
| 31–33 | Bug fixing (prioritized by demo impact) |
| 33–35 | Demo prep: preprocess corpus, verify every demo click, record fallback |
| 35–36 | **Freeze; backup; final verification** (clean clone → run.sh → demo) |

## 9. Agent Boundaries & Ownership (in 05/08 docs)

| Agent | Responsibility | Owns |
|---|---|---|
| A — Foundation | Repo scaffold, DB schema, config, LLM client, sample corpus, eval golden set | `backend/app/{main,config,db,common}/`, `data/sample/`, schema |
| B — Document Intelligence | Upload, OCR, parsing, table extraction, fact extraction | `backend/app/{ingestion,ocr,parse,extraction}/` |
| C — Knowledge & RAG | Chunking, embeddings, vector+BM25, hybrid retrieval, QA | `backend/app/{knowledge,qa}/` |
| D — Analytics | TF-IDF, topics, word cloud, timeseries | `backend/app/analytics/` |
| E — Reports & Review | 2 templates, claim validation, export, review API | `backend/app/{reports,review}/` |
| F — Frontend & Integration | Streamlit screens, API integration, e2e polish | `frontend/`, scripts |

**Shared files** (edit only when required): `docs/`, `PROJECT_STATE.md`, `08_AGENT_HANDOFF.md`, `06_DATA_CONTRACTS.md`, `07_API_CONTRACTS.md`. Architecture changes require a new ADR in `09_DECISIONS_LOG.md` — never silently reverse a FINAL decision.

## 10. Cut List (brutal)

**REMOVE:** knowledge graph, fine-tuning, custom NER training, reranker, Postgres, microservices, Docker (P2), auth/RBAC (P2), PDF export, BERTopic, deep archive system, multi-language OCR, vector-db services.
**SIMPLIFY:** cross-document reasoning → fact aggregation; human review → approve/edit/reject per claim + report approve; topic model → NMF with top-term labels (LLM labels optional P1); report templates → exactly 2.

## 11. Fallback Strategy

| Dependency | Primary | Fallback | Emergency |
|---|---|---|---|
| OCR | PaddleOCR | Tesseract | Pre-extracted text committed in repo |
| LLM | Groq Llama 3.3 70B | OpenAI/Gemini if key appears | **Extractive mode** (facts + top passages, templated) |
| Embeddings | sentence-transformers (local) | fastembed/ONNX | BM25-only mode |
| Retrieval | Hybrid numpy+BM25 | BM25 only | Precomputed results for demo questions |
| Export | DOCX | HTML/Markdown | On-screen text |
| Network/API | Live calls | Cached corpus + cached responses | Fully offline demo path |

**Core demo stays functional with zero external services** (Groq down, no network): extraction, retrieval, analytics, extractive answers, report drafts, review, export all work.

## 12. Evaluation (in 10_TESTING_EVALUATION.md; Actual = TBD until run)

| Metric | Dataset | Method | Target |
|---|---|---|---|
| OCR accuracy | 10 scanned pages | char/word accuracy vs golden text | ≥90% |
| Table/fact extraction | 20 known table values | exact value+unit+period match | ≥90% |
| Retrieval hit rate | 20 golden questions | top-5 evidence contains ground truth | ≥85% |
| Grounded answer rate | 20 questions | answer mode != NO_EVIDENCE + citations present | ≥85% |
| Claim supported % | 30 report claims | mechanical validation vs human check | ≥90% |
| Time saved | manual vs AI draft of one reply | stopwatch both | ≥70% |
| Automation % | steps automated / total steps | workflow step count | ≥60% |

## 13. Judge Demo (~7 minutes, in 11_DEMO_FLOW.md)

1. **Story:** parliamentary inquiry arrives at CMPDI. (30 s)
2. **Upload:** one scanned legacy PDF (live OCR of 1 page), one digital PDF, one XLSX. (1.5 min)
3. **Provenance:** page/section explorer shows what was extracted and where. (1 min)
4. **Analytics:** word cloud, topics, production-by-year chart. (1 min)
5. **Ask AI:** cross-document question → evidence cards, citations, refusal demo (ask an unanswerable question). (1 min)
6. **Report:** generate Parliamentary Reply Draft → claim table with SUPPORTED/NEEDS_REVIEW → reviewer approves one claim, edits one → approve → export DOCX. (1.5 min)
7. **Metrics:** time-saved %, extraction accuracy % from eval harness. (30 s)
**Live:** single-page OCR, all retrieval/answers, review clicks. **Precomputed:** full corpus OCR, embeddings, all demo answers pre-verified. **Never live:** full-corpus OCR of a 100-page scan, API key entry, complex table re-OCR.

## 14. Judge Differentiation (all real in the architecture)

1. Legacy **scanned-document intelligence** (OCR + table reconstruction + provenance) — not "chat with PDF"
2. **Structured mining fact layer** (entity/metric/period/value/unit, deterministic-first)
3. **Evidence-level provenance** — every claim → document → page → section → evidence text
4. **Mechanical claim validation** — no "trust the LLM" anywhere
5. **Automated parliamentary reply + geological summary generation**
6. **Human-in-the-loop review** (approve/edit/reject, stored decisions)
7. **Corpus-level analytics** (word clouds, topics, trends)
8. **Quantified time/accuracy/automation metrics** from the eval harness

## 15. Files to Create in Build Mode

```
README.md                              — overview, stack, setup, run, testing, demo, agent protocol
docs/00_PROJECT_CONTEXT.md             — 2–3 min read: what/why/who, core problem, status
docs/01_PROBLEM_STATEMENT.md           — authoritative SIH26023 text + our interpretation (PS wins conflicts)
docs/02_REQUIREMENTS.md                — full requirements matrix, P0/P1/P2, acceptance criteria
docs/03_ARCHITECTURE.md                — diagram, modules, data flows, source of truth for architecture
docs/04_TECH_STACK.md                  — per-tool decision format (choice/why/alternative/risk/fallback)
docs/05_IMPLEMENTATION_PLAN.md         — phases, module order, dependencies, 36-h timeline
docs/06_DATA_CONTRACTS.md              — all JSON schemas (critical for parallel agents)
docs/07_API_CONTRACTS.md               — endpoints, request/response schemas, errors (frontend↔backend contract)
docs/08_AGENT_HANDOFF.md               — live handoff template; every agent MUST update before finishing
docs/09_DECISIONS_LOG.md               — ADRs (incl. ADR-001 monolith+SQLite, ADR-002 Groq, ADR-003 PaddleOCR, ADR-004 no-graph, ADR-005 Streamlit)
docs/10_TESTING_EVALUATION.md          — metrics, datasets, methods, targets, Actual=TBD
docs/11_DEMO_FLOW.md                   — 7-min script, live vs precomputed vs never, fallback
docs/12_KNOWN_ISSUES.md                — issue log (severity/impact/workaround/status)
docs/PROJECT_STATE.md                  — short live state: working/in-progress/blocked/next
```
Plus the agent operating protocol (read the 9 docs → inspect → don't duplicate → implement → test → update state/handoff → record ADRs → state next steps) embedded in 08 and summarized in README. Also scaffold `backend/`, `frontend/`, `data/sample/`, `scripts/`, `requirements.txt`, `run.sh`.

## 16. First Coding Agent

**Agent A (Foundation)** starts first with exactly this task:
> Initialize the repo, create the scaffolded backend/frontend structure and `coal.db` SQLite schema per 06_DATA_CONTRACTS.md, implement `common/llm_client.py` (Groq primary, provider-agnostic, JSON-mode, extractive fallback), generate the synthetic sample corpus into `data/sample/` (digital PDF, scanned-looking legacy PDF, XLSX with known fact values), and write the 20-fact / 20-question golden eval set.

Read first: `00_PROJECT_CONTEXT.md`, `01_PROBLEM_STATEMENT.md`, `02_REQUIREMENTS.md`, `03_ARCHITECTURE.md`, `04_TECH_STACK.md`, `05_IMPLEMENTATION_PLAN.md`, `06_DATA_CONTRACTS.md`, `07_API_CONTRACTS.md`, `09_DECISIONS_LOG.md`, `PROJECT_STATE.md`. While A builds the schema/corpus, B (ingestion) and C (retrieval) can scaffold in parallel — the contracts in 06/07 keep them independent.

**Success criteria for this phase:** all 15 docs + README committed, git initialized, decisions frozen, corpus + golden set ready — and a completely new agent can start from `PROJECT_STATE.md` + `08_AGENT_HANDOFF.md` with zero chat history.