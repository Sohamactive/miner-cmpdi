"""Hybrid evidence retriever — PostgreSQL facts + Qdrant semantic chunks."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from app.common.llm_client import generate_json, generate_json_or_none
from app.extraction.postgres import create_session, search_facts
from app.extraction.models import Fact
from app.knowledge.embeddings import EmbeddingProvider, FastEmbedProvider
from app.knowledge.qdrant_store import QdrantStore
from app.knowledge.retrieval import SemanticRetriever
from app.reports.schemas import CoverageWarning, EvidenceBundle, EvidenceItem

logger = logging.getLogger(__name__)

QUERY_GEN_PROMPT = """You are an evidence retrieval assistant for mining/coal reports.

Given the user question below, generate exactly 3 search queries that would find relevant facts and evidence in a mining knowledge base.

Each query should target different aspects: numerical data, contextual information, and related terminology.

User question: {question}

Return JSON: {{"queries": ["query1", "query2", "query3"]}}
"""

MAX_INPUT_CHARS = 30000


def _fact_to_item(fact: Fact) -> EvidenceItem:
    doc_id = str(fact.document_id or "")
    return EvidenceItem(
        source="fact",
        document_id=doc_id,
        filename=doc_id,
        page_range=fact.page_range,
        text=fact.evidence or "",
        value=fact.value,
        unit=fact.unit,
        metric=fact.metric,
        entity=fact.entity,
        period=fact.period,
        score=1.0,
    )


def _semantic_to_item(result) -> EvidenceItem:
    return EvidenceItem(
        source="chunk",
        document_id=result.document_id,
        filename=result.filename,
        page_range=result.page_range,
        text=result.text,
        score=result.score,
    )


def _generate_queries(question: str) -> list[str]:
    """Use LLM to generate search queries from the user question."""
    prompt = QUERY_GEN_PROMPT.format(question=question)
    result = generate_json_or_none(prompt)
    if result is None:
        # Fallback: use raw question as single query
        return [question]
    queries = [q for q in result.get("queries", []) if isinstance(q, str) and q.strip()]
    return queries if queries else [question]


def _search_qdrant(queries: list[str], embedder: EmbeddingProvider, qdrant: QdrantStore,
                    doc_ids: list[str] | None = None, limit: int = 5) -> list[EvidenceItem]:
    """Search Qdrant semantic index for each query, dedupe by chunk text."""
    retriever = SemanticRetriever(qdrant, embedder)
    seen_texts: set[str] = set()
    items: list[EvidenceItem] = []
    for query in queries:
        for doc_id in doc_ids or [None]:
            results = retriever.search(query, limit=limit, document_id=doc_id)
            for r in results:
                text_key = r.text[:200]  # dedupe by first 200 chars
                if text_key not in seen_texts:
                    seen_texts.add(text_key)
                    items.append(_semantic_to_item(r))
    return items


def _search_facts(question: str, doc_ids: list[str] | None = None, limit: int = 20) -> list[EvidenceItem]:
    """Search PostgreSQL facts. Try LLM-extracted keywords, then raw question."""
    session = create_session()
    try:
        # Try to extract metric/entity/period from question via LLM
        kw_prompt = (
            "Extract mining keywords from this question as JSON. "
            "Return: {\"metric\": \"...\" or null, \"entity\": \"...\" or null, \"period\": \"...\" or null}\n"
            f"Question: {question}"
        )
        kw = generate_json_or_none(kw_prompt)
        metric = kw.get("metric") if kw else None
        entity = kw.get("entity") if kw else None
        period = kw.get("period") if kw else None

        facts = search_facts(session, entity=entity, metric=metric, period=period, limit=limit)

        # Filter by doc_ids if specified
        if doc_ids:
            facts = [f for f in facts if str(f.document_id) in doc_ids]

        return [_fact_to_item(f) for f in facts]
    finally:
        session.close()


def gather_evidence(
    question: str,
    *,
    doc_ids: list[str] | None = None,
    embedder: EmbeddingProvider | None = None,
    qdrant: QdrantStore | None = None,
) -> EvidenceBundle:
    """Gather evidence from both PostgreSQL (facts) and Qdrant (semantic chunks).

    This is Phase 1 of the report pipeline: evidence gathering only, no drafting.
    """
    logger.info("Gathering evidence for question: %s", question[:100])

    if embedder is None:
        embedder = FastEmbedProvider()
    if qdrant is None:
        qdrant = QdrantStore()

    # 1. Generate search queries via LLM
    queries = _generate_queries(question)
    logger.info("Generated %d search queries: %s", len(queries), queries)

    # 2. Search both stores in parallel
    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_facts = pool.submit(_search_facts, question, doc_ids)
        fut_semantic = pool.submit(_search_qdrant, queries, embedder, qdrant, doc_ids)
        fact_items = fut_facts.result()
        chunk_items = fut_semantic.result()

    logger.info("Found %d facts, %d chunks", len(fact_items), len(chunk_items))

    # 3. Check coverage
    warnings: list[CoverageWarning] = []
    if not fact_items:
        warnings.append(CoverageWarning(topic="facts", message="No structured facts found for this question."))
    if not chunk_items:
        warnings.append(CoverageWarning(topic="context", message="No semantic context found for this question."))

    # Truncate long inputs
    total_chars = sum(len(item.text) for item in fact_items + chunk_items)
    if total_chars > MAX_INPUT_CHARS:
        logger.warning("Evidence bundle too large (%d chars), truncating", total_chars)
        # Keep all facts (they're short), trim chunks by score
        chunk_items.sort(key=lambda x: x.score, reverse=True)
        kept: list[EvidenceItem] = []
        running = sum(len(item.text) for item in fact_items)
        for item in chunk_items:
            if running + len(item.text) > MAX_INPUT_CHARS:
                break
            kept.append(item)
            running += len(item.text)
        chunk_items = kept

    bundle = EvidenceBundle(
        facts=fact_items,
        chunks=chunk_items,
        coverage_warnings=warnings,
    )
    logger.info("Evidence bundle ready: %d facts, %d chunks, %d warnings",
                len(bundle.facts), len(bundle.chunks), len(bundle.coverage_warnings))
    return bundle
