# Initials — Project Feasibility and Report Plan

## Project Overview

The team is building an AI-assisted platform for CMPDI and CIL subsidiaries to process geological, mining, and production documents and to answer parliamentary and administrative inquiries. The system is based on the existing SOW proposal generator, which uses FastAPI, a multi-agent pipeline, Gemini models, and Qdrant retrieval, and extends it toward scanned document intelligence, structured fact extraction, evidence-grounded reporting, and human review.

## Feasibility Assessment

The project is feasible for a university-level SIH internal hackathon and as a minimum viable product. The core stack is already proven, since document upload, retrieval, proposal drafting, review, and DOCX export are working. The remaining work is bounded and does not require model training. The main technical risk is ingestion of scanned PDFs and tables at scale, which requires OCR, background jobs, and provenance tracking. With a one-week timeline, a ten-document demo corpus is realistic, while full automation over hundreds of documents should be presented as a roadmap with an evaluation sample rather than a completed claim.

Infrastructure and cost are not blockers. The demo can run locally at zero cost using Gemini free tier, local Qdrant, SQLite, matplotlib, and Docling. Production deployment would require queued workers, object storage, and a managed vector database, but the module boundaries remain the same.

## Report Generation Improvements

The current report output is a plain dump of headings and bullet points. It will be upgraded to a template-driven engine with a cover page, headers and footers, page numbers, a table of contents, fact tables, citation footnotes, and embedded charts and images.

Charts, tables, and images will be generated dynamically and offline at no cost. Fact tables will be rendered with python-docx and reportlab from the SQLite fact layer. Charts will be generated with matplotlib from production figures by year, mine, and metric, exported as PNG in memory, and embedded in both DOCX and PDF. Page crops and maps from ingestion will be embedded as evidence images. Templates will resolve slots such as production charts and fact tables at generation time and will skip gracefully when data is absent.

Both DOCX and PDF output are required. DOCX is the editable deliverable for CIL and Ministry workflows, while PDF is the archival version generated from the same content through reportlab. PPTX is not required for this use case.

Different report styles will be supported through a template and style registry rather than separate exporters. Each report type, such as Parliamentary Reply Draft, Geological Summary, and Executive Brief, will define its section list and content slots, while each style will define fonts, colors, cover layout, and header treatment. New styles can therefore be added through configuration without code changes.

## Document Classifier for Ingestion

The team will implement a document classifier that routes files before heavy processing. Digital PDFs will be parsed directly with pdfplumber and python-docx, which is fast and preserves tables and coordinates. Scanned PDFs and images will be routed to Docling for OCR, layout analysis, and table reconstruction. Spreadsheets will be handled with openpyxl. Classification will use a lightweight probe, such as extracted text length over the first two pages, with metadata recording whether a document was digital or scanned and which engine processed it. If digital parsing yields no text or facts, the document will be re-queued as scanned.

## Scaling to One Thousand to Two Thousand Documents

For the hackathon, ten pre-ingested documents are sufficient. Hypothetically scaling to one or two thousand documents would require queued ingestion with multiple Docling workers, object storage for files, deduplication by file hash, incremental re-embedding of changed pages only, and persistent job tracking in Postgres rather than SQLite or in-memory state. Retrieval would move to sharded vector search with metadata filtering by year, mine, and subsidiary, hybrid dense and BM25 fusion, result caching, and deterministic fact lookup as the primary path for numeric questions. LLM usage would be restricted to ambiguous extraction and final drafting to control cost and latency, with audit logging, versioned reports, role-based review, and nightly re-indexing added for operational use.

## Conclusion for the Internal Hackathon

With one week of work, the team should freeze ingestion early, deliver one polished Parliamentary Reply template with a table and a chart, demonstrate three verified questions plus one refusal case, and present time-saved and extraction-accuracy figures from a small golden set. This scope is sufficient to clear the internal round and provides a credible foundation for SIH finals.

## Problem Statement Assessment

The problem statement does not explicitly mention RAG, LLMs, OCR, or chatbots. It asks for an automated report generation platform, a word cloud and topic identification module, and an AI-based query and response system, along with validation, consistency, traceability, and phased delivery. The technical approach using retrieval, OCR, structured facts, and grounded answers is the team's interpretation of those outcomes.

This is an underrated problem statement. Most student teams avoid it because coal and mining reports sound unglamorous, the wording resembles enterprise delivery with phases and training, word clouds sound outdated, and the hidden difficulty of scanned tables and accuracy requirements is high. As a result, competition is lower than for generic chatbot or drone statements. The advantage is that judges from the coal sector know exactly what good looks like, namely a correct cited number delivered quickly. The risk is that any hallucinated production figure will be caught immediately.

As an idea independent of infrastructure, it is finalist-grade for its category if built well. It addresses a real manual workflow, covers all three desired modules through one ingestion pipeline, and adds a defensible distinction over simple PDF chat through structured facts, page-level citations, mechanical claim validation, and human review. It should be pitched as a parliamentary question in and a cited reply draft out in minutes, rather than as a generic document platform.

## Quantified Benefits and Verification

The problem statement explicitly asks for quantified benefits in report preparation time, extraction and generation accuracy, and   automation coverage. These provide direct scoring opportunities because few teams measure them. The team will maintain a golden set of twenty facts with document, page, entity, metric, period, value, and unit, plus twenty questions with expected evidence locations.

Extraction accuracy will be verified by comparing ingested facts against the golden set on value, unit, and period, with spot checks of evidence text against source pages. Time saved will be verified with stopwatch comparison between manual compilation and the AI-assisted flow using the formula of manual time minus AI time divided by manual time. Automation coverage will be verified by counting automated workflow steps against total steps. Grounded answer rate will be verified by counting answers that carry correct citations against the twenty golden questions, including a demonstrated refusal case where no evidence exists. All datasets and a simple evaluation script will be stored in the repository so judges can rerun the checks and inspect one source page directly.
