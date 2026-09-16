"""QA responder: fact-first retrieval + semantic fallback + mechanical validation.

Logic:
1. Try exact match in PostgreSQL facts table (entity + metric + period filtered).
2. If hit → run mechanical validator on the fact → return SUPPORTED/NEPEDS_REVIEW/UNSUPPORTED.
3. If miss → semantic search via Qdrant → LLM drafts answer from chunks → run validator on drafted claims.
4. Every claim in the response is validated before returning.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Optional

from app.common.validator import validate_claim, ClaimResult, ClaimStatus
from app.qa.models import QAClaim, QAResponse
from app.extraction.postgres import create_session, search_facts
from app.knowledge.retrieval import SemanticRetriever
from app.knowledge.embeddings import FastEmbedProvider
from app.knowledge.qdrant_store import QdrantStore


@dataclass
class Responder:
    """Respond to a question with cited, validated claims."""

    question: str
    document_id: Optional[str] = None

    # Cached / injected deps (set by caller or lazily)
    _session = None
    _retriever = None
    _embedder = None

    @property
    def session(self):
        if self._session is None:
            self._session = create_session()
        return self._session

    @property
    def retriever(self):
        if self._retriever is None:
            self._retriever = SemanticRetriever(QdrantStore(path="/Users/krish/miner-cmpdi/qdrant_storage"), FastEmbedProvider())
        return self._retriever

    @property
    def embedder(self):
        if self._embedder is None:
            self._embedder = FastEmbedProvider()
        return self._embedder

    def answer(self) -> QAResponse:
        """Run the full fact-first + RAG pipeline and return a validated QAResponse."""
        response = QAResponse(answer_text="", claims=[])

        # ── Step A: Exact fact lookup ──────────────────────────────────────
        facts = search_facts(
            self.session,
            entity=None,
            metric=self.question,
            period=None,
            limit=10,
        )

        if facts:
            # Use the best-matching fact (first result)
            fact = facts[0]
            result = validate_claim(
                value=fact.value,
                unit=fact.unit,
                entity=fact.entity,
                period=fact.period,
                evidence_text=fact.evidence,
                document_id=fact.document_id,
                page_range=fact.page_range,
            )
            claim = QAClaim(
                value=fact.value,
                unit=fact.unit,
                document_id=fact.document_id,
                page_range=fact.page_range,
                evidence_snippet=fact.evidence,
                status=result.status,
            )
            # Build a simple answer text from the fact
            answer_parts = []
            if fact.metric:
                answer_parts.append(f"The {fact.metric}")
            if fact.value is not None:
                answer_parts.append(f"was {fact.value}")
            if fact.unit:
                answer_parts.append(f"{fact.unit}")
            if fact.period:
                answer_parts.append(f"({fact.period})")
            answer_text = " ".join(answer_parts) if answer_parts else str(fact.value)

            response.answer_text = answer_text
            response.claims = [claim]
            return response

        # ── Step B: Semantic fallback via Qdrant ────────────────────────────
        embedder = self.embedder
        results = self.retriever.search(
            self.question, limit=3, document_id=self.document_id
        )

        if not results:
            response.answer_text = "No reliable evidence found in the corpus."
            return response

        # Draft answer text from chunk texts (simple extractive draft)
        context_parts = []
        for r in results:
            context_parts.append(f"[{r.filename} p.{r.page_range or '?'}]: {r.text[:300]}")
        context = "\n\n".join(context_parts)

        # Simple extractive draft: pull sentences that contain numeric values
        answer_text = _draft_answer_from_context(self.question, context)

        # Validate any numeric claims we can extract from the drafted answer
        claims = _validate_claims_from_draft(answer_text, results, embedder)

        response.answer_text = answer_text
        response.claims = claims
        return response


def _draft_answer_from_context(question: str, context: str) -> str:
    """Simple extractive draft: return the sentence from context that best matches the question."""
    import re
    sentences = [s.strip() for s in context.replace("\n", " ").split(".") if s.strip()]
    q_tokens = set(w.lower() for w in question.split() if len(w) > 2)
    best = ""
    best_score = -1
    for s in sentences:
        s_tokens = set(w.lower() for w in s.split() if len(w) > 2)
        score = len(q_tokens & s_tokens)
        if score > best_score:
            best_score = score
            best = s
    if best:
        return best + "."
    # Fallback: first sentence
    return sentences[0] + "." if sentences else ""


def _validate_claims_from_draft(
    answer_text: str,
    qdrant_results,
    embedder: FastEmbedProvider,
) -> list[QAClaim]:
    """Extract numeric claims from the answer text and validate them against Qdrant chunk evidence.

    This is a best-effort validator for the RAG fallback path.
    """
    from app.common.validator import validate_claim, ClaimStatus

    claims: list[QAClaim] = []

    # Extract "VALUE UNIT" patterns from answer text, e.g. "12,400 tonnes", "5,867 persons"
    value_pattern = r"-?\d[\d,]*(?:\.\d+)?\s*(?:%|tonnes|g/t|persons|lakhs|crores|Rs\.?|million|billion)?"
    for m in re.finditer(value_pattern, answer_text, re.IGNORECASE):
        chunk_text = m.group(0)
        # Find the chunk that best matches this text
        best_result = None
        best_score = -1
        for r in qdrant_results:
            # Simple overlap score: how many words overlap
            r_words = set(str(r.text).lower().split())
            chunk_words = set(chunk_text.lower().split())
            overlap = len(r_words & chunk_words)
            if overlap > best_score:
                best_score = overlap
                best_result = r

        if best_result is None:
            continue

        # Parse value and unit from the matched chunk text
        # The chunk text has the form: "Mine X produced 12,400 tonnes during..."
        # We need to extract the number+unit that appears in both answer and chunk
        extracted = _extract_number_unit(chunk_text)
        if not extracted:
            continue

        value, unit = extracted
        # Validate against the chunk evidence (the chunk text itself is the evidence)
        result = validate_claim(
            value=value,
            unit=unit,
            entity=None,
            period=None,
            evidence_text=best_result.text,
            document_id=best_result.document_id,
            page_range=best_result.page_range,
        )

        claims.append(
            QAClaim(
                value=value,
                unit=unit,
                document_id=best_result.document_id,
                page_range=best_result.page_range,
                evidence_snippet=best_result.text[:200],
                status=result.status,
            )
        )

    # Deduplicate claims by (value, unit, document_id)
    seen = set()
    unique: list[QAClaim] = []
    for c in claims:
        key = (str(c.value), c.unit, c.document_id)
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def _extract_number_unit(text: str) -> tuple[float | int | str, str | None] | None:
    """Extract a number and optional unit from text.

    Returns (value, unit) or None.
    """
    import re
    # Pattern: number followed by optional unit word
    m = re.search(
        r"-?\d[\d,]*(?:\.\d+)?\s*(%|tonnes?|g/t|persons?|lakhs?|crores?|Rs\.?|million|billion)?",
        text,
        re.IGNORECASE,
    )
    if not m:
        return None
    raw = m.group(0)
    # Split number from unit
    parts = raw.rsplit(" ", 1)
    number_str = parts[0].replace(",", "")
    try:
        value = float(number_str) if "." in number_str else int(number_str)
    except ValueError:
        try:
            value = float(number_str)
        except ValueError:
            return None
    unit = parts[1].lower() if len(parts) > 1 else None
    return value, unit