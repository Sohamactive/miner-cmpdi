"""QA responder: fact-first retrieval + semantic fallback + LLM generation + mechanical validation.

Logic:
1. Try structured fact lookup in PostgreSQL (entity + metric + period extracted from question).
2. If hit → run mechanical validator on the fact → return SUPPORTED/NEEDS_REVIEW/UNSUPPORTED.
3. If miss → semantic search via Qdrant → LLM generates answer from chunks → validate claims.
4. Every claim in the response is validated before returning.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import List, Optional

from app.common.llm_client import generate_json, generate_json_or_none
from app.common.validator import validate_claim, ClaimStatus
from app.review.qa.models import QAClaim, QAResponse
from app.extraction.postgres import create_session, search_chunks, search_facts
from app.knowledge.retrieval import SemanticRetriever
from app.knowledge.embeddings import FastEmbedProvider
from app.knowledge.qdrant_store import QdrantStore


@dataclass
class Responder:
    """Respond to a question with cited, validated claims."""

    question: str
    document_id: Optional[str] = None
    conversation_history: Optional[List[dict]] = None

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
            self._retriever = SemanticRetriever(
                QdrantStore(),
                FastEmbedProvider()
            )
        return self._retriever

    @property
    def embedder(self):
        if self._embedder is None:
            self._embedder = FastEmbedProvider()
        return self._embedder

    def answer(self) -> QAResponse:
        """Run the full fact-first + RAG pipeline and return a validated QAResponse."""
        response = QAResponse(answer_text="", claims=[])
        retrieval_question = _build_retrieval_question(
            self.question,
            self.conversation_history,
        )

        # ── Step A: Structured fact lookup ───────────────────────────────────
        parsed = _parse_question_for_facts(self.question)
        # Never answer a broad question with the first arbitrary fact in the
        # table. At least one meaningful filter must be present.
        facts = (
            search_facts(
                self.session,
                entity=parsed.get("entity"),
                metric=parsed.get("metric"),
                period=parsed.get("period"),
                limit=5,
            )
            if parsed
            else []
        )

        if facts:
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
            answer_parts = []
            if fact.metric:
                answer_parts.append(f"The {fact.metric}")
            if fact.value is not None:
                answer_parts.append(f"was {_format_value(fact.value)}")
            if fact.unit:
                answer_parts.append(f"{fact.unit}")
            if fact.period:
                answer_parts.append(f"({fact.period})")
            answer_text = " ".join(answer_parts) if answer_parts else str(fact.value)

            response.answer_text = answer_text
            response.claims = [claim]
            return response

        # ── Step B: Semantic fallback via Qdrant + LLM ───────────────────────
        lexical_results = _chunk_results(
            search_chunks(
                self.session,
                retrieval_question,
                document_id=self.document_id,
                limit=5,
            )
        )
        results = self.retriever.search(
            retrieval_question, limit=5, document_id=self.document_id
        )

        # Overview questions are better served by chunks containing the named
        # entity than by nearest-neighbour numeric tables.
        if parsed.get("entity") and not parsed.get("metric") and lexical_results:
            results = lexical_results
        elif not results:
            results = lexical_results

        if not results:
            response.answer_text = "No reliable evidence found in the corpus."
            return response

        # Build context from retrieved chunks
        context_parts = []
        for r in results:
            context_parts.append(f"[Source: {r.filename}, pages {r.page_range or '?'}] {r.text}")
        context = "\n\n".join(context_parts)

        # Call LLM with structured prompt
        llm_result = _call_llm_with_context(
            question=self.question,
            context=context,
            conversation_history=self.conversation_history,
        )

        if llm_result is None:
            # Fallback to extractive if LLM fails
            answer_text = _draft_answer_from_context(self.question, context)
            claims = _validate_claims_from_draft(answer_text, results, self.embedder)
            response.answer_text = answer_text
            response.claims = claims
            return response
        # Parse LLM response (expected JSON with answer_text and claims)
        answer_text = llm_result.get("answer_text", "")
        raw_claims = llm_result.get("claims", [])

        # Validate each claim against retrieved evidence
        validated_claims = _validate_llm_claims(
            raw_claims,
            results,
            period=parsed.get("period"),
        )
        usable_claims = [
            claim
            for claim in validated_claims
            if claim.status in {ClaimStatus.SUPPORTED, ClaimStatus.NEEDS_REVIEW}
        ]
        if not validated_claims and answer_text.strip():
            unavailable = "information is not available" in answer_text.lower()
            if not unavailable:
                response.answer_text = answer_text
                return response

        if not usable_claims and parsed.get("entity") and results:
            response.answer_text = _draft_overview_response(
                parsed["entity"],
                results,
            )
            response.claims = [
                QAClaim(
                    value="Overview",
                    document_id=results[0].document_id,
                    page_range=results[0].page_range,
                    evidence_snippet=results[0].text[:300],
                    status=ClaimStatus.NEEDS_REVIEW,
                )
            ]
            return response

        if not usable_claims:
            response.answer_text = "The information is not available in the provided documents."
            response.claims = []
            return response

        if len(usable_claims) != len(validated_claims):
            verified_values = ", ".join(
                f"{_format_value(claim.value)}{f' {claim.unit}' if claim.unit else ''}"
                for claim in usable_claims
            )
            answer_text = (
                "I could verify only these values from the cited evidence: "
                f"{verified_values}. Other generated figures were not supported."
            )

        response.answer_text = answer_text
        response.claims = usable_claims
        return response


def _build_retrieval_question(
    question: str,
    conversation_history: Optional[List[dict]],
) -> str:
    """Keep the current wording while adding context for conversational follow-ups."""
    if not conversation_history:
        return question

    previous_user_messages = [
        str(message.get("content", "")).strip()
        for message in conversation_history[-6:]
        if message.get("role") == "user" and str(message.get("content", "")).strip()
    ]
    if not previous_user_messages:
        return question

    current_lower = question.lower()
    follow_up_markers = (
        "it", "its", "they", "them", "that", "those", "more", "also",
        "what about", "how about", "and ", "why ", "how many",
    )
    if any(marker in current_lower for marker in follow_up_markers):
        return f"{previous_user_messages[-1]}\nFollow-up: {question}"
    return question


def _chunk_results(chunks) -> list:
    """Adapt PostgreSQL chunks to the semantic result contract used by QA."""
    from app.knowledge.retrieval import SemanticResult

    return [
        SemanticResult(
            score=1.0,
            text=chunk.text,
            document_id=chunk.document_id,
            filename=chunk.filename,
            page_range=chunk.page_range,
            batch=chunk.batch,
            section=chunk.section,
        )
        for chunk in chunks
    ]


def _draft_overview_response(entity: str, results: list) -> str:
    """Provide a useful, explicitly qualified overview when no numeric claim is needed."""
    best = next(
        (result for result in results if entity.lower() in result.text.lower()),
        results[0],
    )
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", best.text.replace("\n", " "))
        if sentence.strip()
    ]
    excerpt = next(
        (
            sentence
            for sentence in sentences
            if "under the ministry of coal" in sentence.lower()
            or "administrative ministry" in sentence.lower()
        ),
        next(
            (
                sentence
                for sentence in sentences
                if entity.lower() in sentence.lower()
            ),
            sentences[0] if sentences else best.text[:300],
        ),
    )
    return (
        f"The indexed documents do not contain a standalone profile of {entity}. "
        f"They do show this relationship in the available evidence: {excerpt} "
        "Ask a follow-up about its companies, production, manpower, or a specific year."
    )


def _parse_question_for_facts(question: str) -> dict:
    """Extract entity, metric, period hints from natural language question."""
    q_lower = question.lower()
    result = {}

    # Common entity patterns
    entities = [
        "ecl", "bccl", "ccl", "wcl", "nec", "cmpdil", "cil",
        "eastern coalfields", "bharat coking coal", "central coalfields",
        "western coalfields", "north eastern coalfields", "cmpdi"
    ]
    for ent in entities:
        if ent in q_lower:
            result["entity"] = ent.upper() if len(ent) <= 5 else ent.title()
            break

    # Period patterns
    period_match = re.search(r"(19|20)\d{2}[-/](\d{2}|\d{4})", question)
    if period_match:
        result["period"] = period_match.group(0).replace("-", ".")
    else:
        period_match = re.search(r"31\.?3\.?(19|20)\d{2}", question)
        if period_match:
            result["period"] = period_match.group(0)
        else:
            year_match = re.search(r"\b((?:19|20)\d{2})\b", question)
            if year_match:
                result["period"] = year_match.group(1)

    # Metric keywords
    metric_keywords = {
        "executive": "executives",
        "manpower": "manpower",
        "strike": "strikes",
        "capital expenditure": "capital expenditure",
        "profit": "profit",
        "loss": "profit/loss",
        "production": "production",
        "revenue": "revenue",
        "royalty": "royalty",
        "cess": "cess",
        "sales tax": "sales tax",
        "persons trained": "persons trained",
        "training": "persons trained",
    }
    for kw, metric in metric_keywords.items():
        if kw in q_lower:
            result["metric"] = metric
            break

    if "ministry of coal" in q_lower:
        result["entity"] = "Ministry of Coal"

    return result


def _format_value(value: float | int | str) -> str:
    """Format numeric value preserving decimals."""
    if isinstance(value, (int, float)):
        v = float(value)
        if v == int(v):
            return str(int(v))
        return f"{v:g}"
    return str(value)


def _call_llm_with_context(
    question: str,
    context: str,
    conversation_history: Optional[List[dict]] = None,
) -> dict | None:
    """Call Bedrock LLM with question, context, and optional history."""
    # Build conversation context
    history_text = ""
    if conversation_history:
        history_parts = []
        for msg in conversation_history[-4:]:  # Last 4 messages
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_parts.append(f"{role}: {content}")
        history_text = "\n\nConversation history:\n" + "\n".join(history_parts)

    prompt = f"""You are an AI assistant for mining reports. Answer the question using ONLY the provided context.

{history_text}

Context from documents:
{context}

Question: {question}

Rules:
1. Answer ONLY using information from the provided context.
2. If the answer is not in the context, say "The information is not available in the provided documents."
3. Preserve exact numerical values including decimals (e.g., 13.66, not 13).
4. Include units with numbers (e.g., "13.66 crores", "6,69,273 persons").
5. Cite sources using [filename, pages] format from the context.

Return JSON with exactly these fields:
{{
  "answer_text": "your complete answer here",
  "claims": [
    {{
      "value": 13.66,
      "unit": "crores",
      "source_reference": "[filename, pages]"
    }}
  ]
}}

Each claim must have value (number), unit (string or null), and source_reference (string). Only include claims for facts explicitly stated in the context."""

    return generate_json_or_none(prompt)


def _validate_llm_claims(
    raw_claims: list,
    qdrant_results,
    *,
    period: str | None = None,
) -> list[QAClaim]:
    """Validate LLM-extracted claims against retrieved chunks."""
    from app.common.validator import validate_claim

    claims: list[QAClaim] = []

    for rc in raw_claims:
        if not isinstance(rc, dict):
            continue
        value = rc.get("value")
        unit = rc.get("unit")
        source_ref = rc.get("source_reference", "")

        # Find matching chunk
        best_result = None
        best_score = -1
        for r in qdrant_results:
            r_text = f"{r.filename} {r.page_range or ''}"
            if r_text.lower() in source_ref.lower() or source_ref.lower() in r_text.lower():
                best_result = r
                break
            # Fallback: word overlap
            r_words = set(str(r.text).lower().split())
            ref_words = set(source_ref.lower().split())
            overlap = len(r_words & ref_words)
            if overlap > best_score:
                best_score = overlap
                best_result = r

        if best_result is None:
            continue

        # Normalize value
        try:
            if isinstance(value, str):
                value = float(value.replace(",", ""))
        except (ValueError, TypeError):
            continue

        result = validate_claim(
            value=value,
            unit=unit,
            entity=None,
            period=period,
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
                evidence_snippet=best_result.text[:300],
                status=result.status,
            )
        )

    # Deduplicate
    seen = set()
    unique: list[QAClaim] = []
    for c in claims:
        key = (str(c.value), c.unit, c.document_id)
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def _draft_answer_from_context(question: str, context: str) -> str:
    """Fallback extractive draft if LLM fails."""
    sentences = [s.strip() for s in context.replace("\n", " ").split(".") if s.strip()]
    q_tokens = set(w.lower() for w in question.split() if len(w) > 2)
    
    # Score sentences by relevance to question
    scored = []
    for s in sentences:
        s_tokens = set(w.lower() for w in s.split() if len(w) > 2)
        score = len(q_tokens & s_tokens)
        # Boost score for sentences with numbers and units
        if re.search(r"\d[\d,]*(?:\.\d+)?\s*(?:%|crores?|lakhs?|tonnes?|persons?|million|billion|Rs)", s, re.IGNORECASE):
            score += 2
        # Boost for sentences with question keywords
        if any(kw in s.lower() for kw in ["executive", "manpower", "strike", "capital", "profit", "production", "royalty", "cess", "tax", "training"]):
            score += 1
        # Penalize very short or fragment sentences
        if len(s) < 20:
            score -= 3
        scored.append((score, s))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored and scored[0][0] > 0:
        return scored[0][1] + "."
    # Fallback: return first substantial sentence with a number
    for s in sentences:
        if re.search(r"\d", s) and len(s) > 30:
            return s + "."
    return sentences[0] + "." if sentences else ""


def _validate_claims_from_draft(
    answer_text: str,
    qdrant_results,
    embedder: FastEmbedProvider,
) -> list[QAClaim]:
    """Fallback claim extraction from extractive draft.
    
    Only extracts the most relevant claim for the question.
    """
    from app.common.validator import validate_claim

    claims: list[QAClaim] = []

    # Extract question keywords for relevance filtering
    q_keywords = set(w.lower() for w in answer_text.split() if len(w) > 3)
    
    # Pattern for numbers with units - most reliable signals
    value_pattern = r"-?\d[\d,]*(?:\.\d+)?\s*(?:%|tonnes?|g/t|persons?|lakhs?|crores?|Rs\.?|million|billion)"
    
    matches = list(re.finditer(value_pattern, answer_text, re.IGNORECASE))
    
    # If we have explicit unit matches, use the first one (most relevant)
    if matches:
        m = matches[0]
        chunk_text = m.group(0).strip()
        
        best_result = None
        best_score = -1
        for r in qdrant_results:
            r_words = set(str(r.text).lower().split())
            chunk_words = set(chunk_text.lower().split())
            overlap = len(r_words & chunk_words)
            if overlap > best_score:
                best_score = overlap
                best_result = r

        if best_result:
            extracted = _extract_number_unit(chunk_text)
            if extracted:
                value, unit = extracted
                # Skip years
                if not (isinstance(value, (int, float)) and 1900 <= value <= 2100):
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
                            evidence_snippet=best_result.text[:300],
                            status=result.status,
                        )
                    )
    else:
        # No explicit unit match - try to find a relevant number in the answer text
        # Look for the first substantial number (not a year)
        num_pattern = r"-?\d[\d,]*(?:\.\d+)?"
        for m in re.finditer(num_pattern, answer_text):
            try:
                value = float(m.group(0).replace(",", "")) if "." in m.group(0) else int(m.group(0).replace(",", ""))
            except ValueError:
                continue
            # Skip years and very small numbers
            if 1900 <= value <= 2100 or value < 10:
                continue
            
            # Find best matching chunk
            best_result = None
            best_score = -1
            for r in qdrant_results:
                r_words = set(str(r.text).lower().split())
                chunk_words = set(m.group(0).lower().split())
                overlap = len(r_words & chunk_words)
                if overlap > best_score:
                    best_score = overlap
                    best_result = r
            
            if best_result and best_score > 0:
                result = validate_claim(
                    value=value,
                    unit=None,
                    entity=None,
                    period=None,
                    evidence_text=best_result.text,
                    document_id=best_result.document_id,
                    page_range=best_result.page_range,
                )
                claims.append(
                    QAClaim(
                        value=value,
                        unit=None,
                        document_id=best_result.document_id,
                        page_range=best_result.page_range,
                        evidence_snippet=best_result.text[:300],
                        status=result.status,
                    )
                )
                break  # Only take the first relevant number

    return claims


def _extract_number_unit(text: str) -> tuple[float | int, str | None] | None:
    """Extract a number and optional unit from text. Preserves decimals."""
    m = re.search(
        r"(-?\d[\d,]*(?:\.\d+)?)\s*(%|tonnes?|g/t|persons?|lakhs?|crores?|Rs\.?|million|billion)?",
        text,
        re.IGNORECASE,
    )
    if not m:
        return None
    number_str = m.group(1).replace(",", "")
    try:
        value = float(number_str) if "." in number_str else int(number_str)
    except ValueError:
        return None
    unit = m.group(2).lower() if m.group(2) else None
    return value, unit