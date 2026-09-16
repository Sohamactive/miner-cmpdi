"""Versioned, agent-owned report state."""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel, Field

from app.reports.schemas import Claim, EvidenceBundle, ReportSection


class ReportRequestState(BaseModel):
    question: str
    report_type: str
    title: str = ""
    doc_ids: list[str] = Field(default_factory=list)


class SectionState(BaseModel):
    heading: str
    paragraphs: list[str] = Field(default_factory=list)
    fact_ids: list[str] = Field(default_factory=list)
    chart_spec: dict[str, Any] | None = None
    status: str = "pending"
    issues: list[str] = Field(default_factory=list)
    version: int = 1

    @classmethod
    def from_section(cls, section: ReportSection, *, status: str = "drafted") -> "SectionState":
        return cls(**section.model_dump(), status=status)


class ValidationState(BaseModel):
    status: str = "pending"
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    supported: int = 0
    needs_review: int = 0
    unsupported: int = 0


class HumanReviewState(BaseModel):
    status: str = "not_started"
    comments: list[dict[str, Any]] = Field(default_factory=list)


class RevisionTask(BaseModel):
    section: str
    issue_type: str
    instruction: str
    claim_id: str | None = None
    status: str = "pending"


class ReviewComment(BaseModel):
    section: str
    issue_type: str
    comment: str
    severity: str = "medium"
    claim_id: str | None = None


class ExportState(BaseModel):
    status: str = "not_ready"
    path: str | None = None


class StateChange(BaseModel):
    agent: str
    fields: list[str]
    timestamp: float = Field(default_factory=time.time)


class AgentLog(BaseModel):
    agent: str
    status: str
    duration_seconds: float = 0.0
    error: str | None = None
    timestamp: float = Field(default_factory=time.time)


class ReportState(BaseModel):
    schema_version: int = 1
    state_version: int = 1
    report_id: int | None = None
    status: str = "drafting"
    request: ReportRequestState
    evidence: EvidenceBundle = Field(default_factory=EvidenceBundle)
    outline: list[str] = Field(default_factory=list)
    sections: dict[str, SectionState] = Field(default_factory=dict)
    claims: list[Claim] = Field(default_factory=list)
    validation: ValidationState = Field(default_factory=ValidationState)
    human_review: HumanReviewState = Field(default_factory=HumanReviewState)
    revision_tasks: list[RevisionTask] = Field(default_factory=list)
    export: ExportState = Field(default_factory=ExportState)
    change_log: list[StateChange] = Field(default_factory=list)
    agent_logs: list[AgentLog] = Field(default_factory=list)

    def apply_agent_update(
        self,
        agent: str,
        updates: dict[str, Any],
        allowed_fields: set[str],
    ) -> None:
        """Apply only fields owned by agent; reject cross-agent writes."""
        invalid = [field for field in updates if field not in allowed_fields]
        if invalid:
            raise ValueError(f"Agent {agent} cannot update: {', '.join(invalid)}")

        data = self.model_dump()
        for path, value in updates.items():
            target = data
            parts = path.split(".")
            for part in parts[:-1]:
                target = target[part]
            target[parts[-1]] = value
        updated = type(self).model_validate(data)
        self.__dict__.update(updated.__dict__)
        self.state_version += 1
        self.change_log.append(StateChange(agent=agent, fields=list(updates)))
