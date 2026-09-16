"""QA response models for M.I.N.E.R. report QA pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QAClaim:
    """A single claim extracted from a question answer, with validation status."""
    value: float | int | str
    unit: str | None = None
    document_id: str = ""
    page_range: str | None = None
    evidence_snippet: str = ""
    status: str = "UNSUPPORTED"  # SUPPORTED | NEEDS_REVIEW | UNSUPPORTED

    def __post_init__(self) -> None:
        if self.status not in {"SUPPORTED", "NEEDS_REVIEW", "UNSUPPORTED"}:
            self.status = "UNSUPPORTED"


@dataclass
class QAResponse:
    """Structured answer from the QA system."""
    answer_text: str = ""
    claims: List[QAClaim] = field(default_factory=list)