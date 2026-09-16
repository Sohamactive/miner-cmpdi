"""QA API endpoint for M.I.N.E.R. question answering.

POST /api/qa/ask
Body: {
  "question": "How many executives did ECL have as of 31.3.84?",
  "document_id": "...",
  "conversation_history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
}
Returns: {"answer_text": "...", "claims": [{"value": ..., "unit": ..., "document_id": ..., "page_range": ..., "evidence_snippet": ..., "status": "SUPPORTED"}]}
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.qa.responder import Responder
from app.qa.models import QAResponse


router = APIRouter()


class QARequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question to answer from indexed reports")
    document_id: str | None = Field(default=None, description="Optional document identifier filter")
    conversation_history: list[dict] | None = Field(
        default=None,
        description="Optional conversation history for follow-up questions. Each entry: {'role': 'user|assistant', 'content': '...'}"
    )


@router.post("/ask", response_model=QAResponse, tags=["qa"])
def ask_question(
    body: QARequest,
) -> QAResponse:
    """Ask a question about the mining reports and get a cited, validated answer."""
    responder = Responder(
        question=body.question,
        document_id=body.document_id,
        conversation_history=body.conversation_history,
    )
    result: QAResponse = responder.answer()

    if not result.answer_text and not result.claims:
        raise HTTPException(
            status_code=404,
            detail="No reliable evidence found for this question.",
        )

    return result