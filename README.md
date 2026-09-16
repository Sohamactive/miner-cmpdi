# ⛏️ M.I.N.E.R. — Mining Intelligence, Knowledge & Evidence Reporter
### Smart India Hackathon 2026 · Problem Statement SIH26023

> **An AI platform that turns decades of scanned CMPDI/CIL mining reports into cited parliamentary replies in minutes — not days.**

[![SIH 2026](https://img.shields.io/badge/SIH-2026-orange?style=for-the-badge)](https://sih.gov.in)
[![PS ID](https://img.shields.io/badge/PS_ID-SIH26023-blue?style=for-the-badge)](#-problem-statement)
[![Status](https://img.shields.io/badge/Status-Working_Prototype-green?style=for-the-badge)](#-whats-working-today)
[![Stack](https://img.shields.io/badge/Stack-FastAPI_%2B_React_%2B_PostgreSQL_%2B_Qdrant-purple?style=for-the-badge)](#-tech-stack)


---

## 📌 Problem Statement

**CMPDI/CIL subsidiaries** must answer **parliamentary and high-priority Ministry of Coal inquiries** by compiling data from **scanned PDFs, digital documents, spreadsheets, images, and historical archives**. Today this is fully manual:

| Pain | Reality |
|---|---|
| 🐢 **Slow** | One reply takes **days** of hunting through annual reports |
| ❌ **Error-prone** | Figures are **hand-copied** from tables — no validation |
| 🔍 **Untraceable** | No link from a number back to its **source page** |
| 👤 **Expert-dependent** | Only senior analysts know *where* each figure lives |

**The PS demands 3 modules:** ① Automated Report Generation Platform · ② Word Cloud + Topic Identification · ③ AI-Based Query & Response System — plus quantified **time-saved %, accuracy %, automation %**.

---

## 💡 Our Solution

**M.I.N.E.R.** converts table-heavy legacy scans into a **structured, provably-sourced fact layer** (`{entity, metric, period, value, unit, doc, page, evidence}`) and builds everything on top of it:

```
📤 Upload scanned PDF / XLSX / image
        ↓  Docling OCR + table reconstruction (page-level provenance)
📚 Structured evidence  →  PostgreSQL (facts + chunks + raw JSONB)
        ↓                       ↓
🔍 Facts-first QA  +  🎯 Semantic search (Qdrant mirror)
        ↓
📝 Cited Parliamentary Reply → ✅ Mechanical validation → 🧑‍⚖️ Human review → 📄 DOCX
📊 Word clouds, topics & production trend charts from the same corpus
```

**The golden rule: AI drafts, code validates.** Every number must carry `{document, page_range, evidence}` or it is quarantined — never exported. When evidence is missing, the system **refuses** instead of hallucinating.

---

## ✨ Key Features (mapped to the PS)

| PS Outcome | What we built | Status |
|---|---|---|
| **① Automated Report Generation** | Parliamentary Reply + Geological Summary templates; fact tables, matplotlib charts, citation footnotes, DOCX export; human-in-the-loop feedback → revise (v1, v2…) → approve | 🟡 Building (pipeline + jobs + export live) |
| **② Word Cloud + Topics** | TF-IDF/NMF analytics, Topic Explorer page, production-by-year charts (Recharts) | 🟢 Frontend live on mock data; backend `analytics/` wiring in progress |
| **③ AI Query & Response** | AI Query page (streaming, follow-ups); facts-first PostgreSQL lookup → Qdrant semantic fallback; cross-document compare by year/mine/metric; refusal on no evidence | 🟢 Prototype live (`POST /api/qa/ask`) |
| **Trust layer (cross-cutting)** | Citation chips on every claim; mechanical `SUPPORTED / NEEDS_REVIEW / UNSUPPORTED` validation; review & approval screen | 🟢 Validator + review service live |
| **Multi-modal ingestion** | PDF (scanned + digital), XLSX/XLS/CSV, PNG/JPG/TIFF — parallel 3-page batches, fallback presets, PyMuPDF emergency salvage, artifact-based resume | 🟢 Implemented |

**UI screens:** 📊 Dashboard · 🤖 AI Query (streaming) · 🧭 Topic Explorer · 📝 Report Synthesis · ✅ Review & Approval — in a gov-portal styled React app.

---

## 🆚 Why We Win (innovation + feasibility)

1. **Scanned-document intelligence, not "chat with PDF"** — OCR + table reconstruction with page provenance on 1980s degraded scans.
2. **Deterministic fact layer** — numbers live in PostgreSQL with exact entity/metric/period filtering; vectors are only a *rebuildable mirror*.
3. **Zero-hallucination policy** — mechanical code validation + refusal; judges can click any number → source page.
4. **Works offline in the demo room** — local FastEmbed embeddings + extractive fallback; no API key needed for retrieval, analytics, or export.
5. **Quantified impact** — golden 20-facts / 20-questions eval harness → time-saved %, accuracy %, automation % on the PPT slide.

---

## 🛠️ Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Ingestion | **Docling** (EasyOCR, Accurate/Fast table modes) + **PyMuPDF** fallback | Best open table reconstruction on degraded scans; native-code salvage when Docling crashes |
| Backend | **FastAPI** (modular monolith, `uv`) | Typed contracts, auto `/docs`, one deploy; async job APIs for long ingest/index/report runs |
| Structured store | **PostgreSQL** (SQLAlchemy + psycopg, JSONB) | Relational facts + provenance + integrity; `documents/pages/chunks/facts/raw_docling_documents` |
| Semantic index | **Qdrant** (`miner_chunks`) + **FastEmbed** `bge-small-en-v1.5` | Dedicated MINER instance; rebuildable from PG — never authoritative for numbers |
| LLM | **Gemini 2.5 Flash / AWS Bedrock** (provider-agnostic client) | Drafting only — never validation |
| Reports | **python-docx**, **matplotlib** | Editable DOCX deliverable + in-memory charts |
| Frontend | **React 19 + Vite + TS**, Tailwind, Recharts, React Router | 5 gov-portal screens; streaming QA |
| Eval | Golden set + `reports/eval.py` | Time / accuracy / automation % |

**Architecture:** React ↔ FastAPI job APIs (`upload → process → index → ask → generate → review → export`). Modules: `api/ ingestion/ extraction/ knowledge/ qa/ analytics/ reports/ review/ common/` (see `docs/03_ARCHITECTURE.md`).

---



## 🚀 Run It 

**Prerequisites:** `uv`, Node 18+, Docker.

```powershell
# 1. Backend env
Copy-Item .\.env.example .\backend\.env   # then edit DATABASE_URL / QDRANT_URL / LLM keys

# 2. Services (dedicated MINER instances)
docker run -d --name miner-postgres -e POSTGRES_DB=miner_db -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16
docker run -d --name miner-qdrant -p 6334:6333 -v "${PWD}\qdrant_storage_miner:/qdrant/storage" qdrant/qdrant:v1.19.0
# set QDRANT_URL=http://localhost:6334 in backend\.env

# 3. Backend  →  http://localhost:8000/docs
cd backend; uv sync; uv run uvicorn app.main:app --reload

# 4. Frontend (new terminal)
cd frontend; npm install; npm run dev
```

**End-to-end in Swagger (`/docs`):** `POST /api/documents/upload` → `POST /api/documents/{id}/process` → `POST /api/documents/{id}/index-job` (poll `GET /api/documents/index-job/{job_id}`) → `POST /api/qa/ask` → `POST /api/reports/generate-job` (poll `/api/reports/job/{job_id}`) → approve → download DOCX.

> ⚠️ `/process` is synchronous (a 66-page scan ≈ 1–3h on CPU) — ingest your demo corpus **before** judging day. Indexing is a separate step by design.

Full ops guide: [`docs/10_OPERATIONS_RUNBOOK.md`](docs/10_OPERATIONS_RUNBOOK.md) · Full API table: see Developer appendix below.

---

<!-- ## 📊 Impact (fill from eval runs before finals)

| Metric | Method | Target | Actual |
|---|---|---|---|
| ⏱️ Time saved | Manual vs AI draft of one reply | ≥ 70% | *TBD — run eval* |
| 🎯 Extraction accuracy | 20 golden table values (value+unit+period) | ≥ 90% | *TBD* |
| 🤖 Automation | Automated steps / total workflow steps | ≥ 60% | *TBD* |
| 🛡️ Grounded answers | 20 golden Qs with correct citation (+ refusals) | ≥ 85% | *TBD* | -->

## 🔮 Future Scope

Async `/process` jobs · exact per-page markers · richer entity/unit extraction · XLSM/image-native retrieval · full CIL workflow integration + training · 1000-doc scale-out (roadmap, not demo).

---

## 📁 Repo Map

```
docs/        00 context → 01 PS (SIH26023 verbatim) → 02 requirements → 03 architecture
             04 ingestion ✅ → 05 RAG ✅ → 06 reports 🟡 → 09 decisions → 10 runbook
backend/     FastAPI + uv (Python ≥3.12) · app/{api,ingestion,extraction,knowledge,qa,reports,review,analytics,common}
frontend/    React 19 + Vite + TS · pages: Dashboard, AIQuery, TopicExplorer, ReportSynthesis, ReviewApproval
.env.example → copy to backend/.env
```

## 👥 Team *(update before submission)*

| Name | Role |
|---|---|
| _Your Name_ | Team Leader · _area_ |
| _Member 2_ | Backend / Ingestion |
| _Member 3_ | RAG / QA |
| _Member 4_ | Reports / Eval |
| _Member 5_ | Frontend |
| _Member 6_ | _area_ |

**College:** _Name_ · **Mentor:** _Name_

---

<details>
<summary><b>🧑‍💻 Developer appendix — full API table, config & contribution protocol</b></summary>

### API cheatsheet

| Method | Route | What |
|---|---|---|
| `POST` | `/api/documents/upload` | Upload PDF/XLSX/CSV/image → `{doc_id}` (sha256, dedupes) |
| `POST` | `/api/documents/{id}/process` | Run ingestion (sync) |
| `GET` | `/api/documents/{id}/result`, `/merged.md` | Checkpoint JSON / merged markdown |
| `GET` | `/api/documents/uploads`, `/batches` | Inventory + index-readiness flags |
| `POST` | `/api/documents/{id}/index` | Sync index → PG + Qdrant |
| `POST` | `/api/documents/{id}/index-job` | Async index → `{job_id}` |
| `GET` | `/api/documents/index-job/{job_id}` | Poll index job |
| `POST` | `/api/documents/index-all-job` | Bulk async index of ready dirs |
| `POST` | `/api/qa/ask` | Cited answer + validated claims (404 = no evidence) |
| `POST` | `/api/reports/generate` / `/generate-job` | Sync / async report generation |
| `GET` | `/api/reports/job/{job_id}` | Poll report job |
| `GET` | `/api/reports/{id}`, `/claims` | Report JSON + claim flags |
| `POST` | `/api/reports/{id}/feedback` | HITL re-draft (v1 → v2…) |
| `POST` | `/api/reports/{id}/approve` | Sign-off → export-ready |
| `GET` | `/api/reports/{id}/download.docx` | DOCX (approved SUPPORTED claims only) |

### Configuration (`backend/.env`)

`DATABASE_URL` (PG, `…/miner_db`) · `QDRANT_URL` (e.g. `http://localhost:6334`) · `QDRANT_COLLECTION=miner_chunks` · `EMBEDDING_MODEL=BAAI/bge-small-en-v1.5` · `EMBED_BATCH_SIZE` (4–8 on low RAM) · `LLM_PROVIDER=gemini|bedrock` + `GEMINI_API_KEY`/`LLM_MODEL` or `AWS_REGION`/`BEDROCK_MODEL` · `EXPORT_FOLDER=./data/reports`. Never commit `.env`, `backend/data/`, or `qdrant_storage*/`.

### Contribution protocol

Read `docs/00→01→02→03→04` in order (PS wins conflicts); respect backend module boundaries; `uv` only; verify by execution; every number keeps `{doc, page, evidence}`; architecture changes → ADR in `docs/09_DECISIONS_LOG.md`. See `AGENTS.md`.
</details>
