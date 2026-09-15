# 01 — Problem Statement (SIH26023)

> Status: DRAFT — nothing locked. Source: official PS text below. Interpretation follows; PS wins conflicts.

## 1. Verbatim PS

CMPDI/CIL subsidiaries play a key role in providing geological and mining information to the Ministry of Coal and responding to parliamentary and high-priority administrative inquiries. These reports require compilation of data from scanned PDFs, digital documents, spreadsheets, images, and historical archives. The current workflow is largely manual, resulting in:

- High dependence on individual expertise
- Delay in generating reports and analytics
- Higher probability of manual errors
- Limited ability to quickly retrieve insights when required

Objectives:

- Deploy an automated platform for AI-assisted geological, mining and any other production figures document processing and reporting.
- Enhance data validation, consistency, and traceability across historical and contemporary datasets.
- Build an efficient, scalable foundation for future digital transformation initiatives within each CIL subsidiary and the Ministry of Coal.

Desired Outcomes: The solution should be implemented in structured phases, including requirement analysis, data digitization and pre-processing, platform development, system testing, integration with CIL subsidiary workflows, training, and continuous enhancement to ensure scalability and long-term adoption.

1. Automated Report Generation Platform
2. Automated Word Cloud and Topic Identification Module
3. AI-Based Query and Response System

Expected Benefits:

- Reduction in report preparation time as less as it can be, quantified in percentage.
- Maximum accuracy, calculated in percentage in structured extraction and report generation.
- Maximum automation, calculated in percentage of repetitive reporting and response workflows.
- Faster response to high-level inquiries and parliamentary questions
- Improved data accessibility, transparency, and standardization
- Strengthened operational efficiency and informed decision-making using historical insights and AI-generated recommendations

Impact:

The proposed system should significantly modernize CMPDI/CIL subsidiaries reporting ecosystem, reduce dependency on manual processes, improve response timelines, and strengthen the coal sector's capability to support governance, policy planning, and operational excellence.

## 2. What this demands (interpretation)

- Inputs: scanned PDFs + digital PDFs + XLSX + images + archives. Numbers in tables are the payload.
- Three modules, not one: reports + word cloud/topics + query/response.

## 3. Non-functional requirements (DRAFT — detail later)

### 3.1 Traceability + validation
- Traceability: every numeric claim links doc → page → evidence text/cell, shown as citation chips on text, table rows, and chart points. Page markers (`<!-- page:N -->`) preserved from ingestion so citations resolve exactly.
- Validation is mechanical (code, not AI): value-in-evidence, unit/year/entity match, citation present → SUPPORTED / NEEDS_REVIEW / UNSUPPORTED.
- Chat policy: SUPPORTED shows with citation; NEEDS_REVIEW shows with yellow flag; UNSUPPORTED shows no number — refusal ("no reliable evidence"). AI drafts, code validates.
- Reports: UNSUPPORTED quarantined in review table (delete/fix), never exported. Final DOCX holds approved SUPPORTED only.

### 3.2 Phased delivery
PS-mandated phases (analysis → digitization → build → test → integrate → train → enhance) mapped to our extended multi-day plan (detail in 05). Demo shows staged progress, not big-bang.

### 3.3 Quantified time / accuracy / automation %
- Time saved = (manual − AI) / manual on one reply draft.
- Accuracy = golden facts matched on value+unit+period; grounded answers with correct citation (incl. refusal cases).
- Automation = automated workflow steps / total steps.
- Method: one-time manual golden set (20 facts / 20 questions), then automated `eval.py` on every run (detail in 10).

### 3.4 Scalable foundation
Modular monolith; schema portable beyond SQLite; queued batch ingestion (fresh process per batch + timeout + resume) so 200+ page reports don't kill the job. Full 1000-doc scale is roadmap, not demo (detail in 03).

