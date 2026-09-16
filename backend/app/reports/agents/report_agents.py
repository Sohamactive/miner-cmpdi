"""Phase-one report agents sharing one validated ReportState."""

from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections.abc import Callable

from app.reports.retrieval import gather_evidence
from app.reports.schemas import EvidenceBundle, ReportSection
from app.reports.validate import extract_claims_from_sections, validate_claims
from app.reports.writer import write_sections
from app.reports.state import ReportState, RevisionTask, SectionState
from app.reports.state import AgentLog
from app.common.llm_client import generate_json
from app.reports.writer import _format_evidence

logger = logging.getLogger(__name__)


class EvidenceAgent:
    name = "evidence_agent"
    owns = {"evidence"}

    def run(self, state: ReportState) -> None:
        evidence = gather_evidence(
            question=state.request.question,
            doc_ids=state.request.doc_ids,
        )
        state.apply_agent_update(
            self.name,
            {"evidence": evidence},
            self.owns,
        )


class DraftAgent:
    name = "draft_agent"
    owns = {"sections"}

    def run(
        self, state: ReportState, template, custom_sections: list[str] | None = None
    ) -> None:
        sections = write_sections(
            question=state.request.question,
            title=state.request.title or template.title,
            template=template,
            evidence=state.evidence,
            custom_sections=custom_sections,
        )
        section_state = {
            section.heading: SectionState.from_section(section) for section in sections
        }
        state.apply_agent_update(self.name, {"sections": section_state}, self.owns)


class SectionAgent:
    """Draft one report section and write only its owned state path."""

    def __init__(self, heading: str, purpose: str) -> None:
        self.heading = heading
        self.name = f"{heading}_agent"
        self.owns = {f"sections.{heading}"}
        self.purpose = purpose

    def draft(self, state: ReportState, feedback: str = "") -> SectionState:
        evidence = _format_evidence(state.evidence)[:30000]
        feedback_block = (
            f"Human review feedback for this section:\n{feedback}\n" if feedback else ""
        )
        prompt = f"""You are the {self.heading} agent in an evidence-grounded mining report.
Write only the {self.heading} section.
Purpose: {self.purpose}
Question: {state.request.question}
{feedback_block}
Evidence:
{evidence}

Return JSON only:
{{"paragraphs": ["..."], "fact_ids": ["F0 or C0"], "chart_spec": null}}

Rules: use only supplied evidence; every numeric statement needs a fact_ids reference;
do not invent values; write 'Data not available.' when evidence is insufficient.
"""
        result = generate_json(prompt)
        section = SectionState(
            heading=self.heading,
            paragraphs=[
                str(value)
                for value in result.get("paragraphs", [])
                if isinstance(value, str)
            ],
            fact_ids=[
                str(value)
                for value in result.get("fact_ids", [])
                if isinstance(value, str)
            ],
            chart_spec=(
                result.get("chart_spec")
                if isinstance(result.get("chart_spec"), dict)
                else None
            ),
            status="drafted",
        )
        return section

    def run(self, state: ReportState, feedback: str = "") -> None:
        state.apply_agent_update(self.name, {f"sections.{self.heading}": self.draft(state, feedback)}, self.owns)


class SpecializedDraftAgent:
    """Run section agents in template order."""

    SECTION_PURPOSES = {
        "preamble": "briefly explain scope, source set, and report objective",
        "overview": "briefly explain scope, source set, and report objective",
        "facts_summary": "summarize important measured facts and comparisons",
        "evidence_table": "introduce the evidence table without duplicating unsupported claims",
        "production_figures": "introduce the production figures table",
        "production_chart": "describe the chart and its evidence-backed trend",
        "trend_chart": "describe the chart and its evidence-backed trend",
        "analysis": "interpret supported trends and comparisons without speculation",
        "conclusion": "summarize supported findings and limitations",
        "recommendations": "give only evidence-grounded recommendations",
        "geological_data": "summarize geological evidence and limitations",
    }

    def run(
        self,
        state: ReportState,
        headings: list[str],
        progress_callback: Callable[[str, str], None] | None = None,
    ) -> None:
        agents = [
            SectionAgent(
                heading,
                self.SECTION_PURPOSES.get(heading, "write a concise evidence-grounded section"),
            )
            for heading in headings
            if heading != "citations"
        ]
        max_workers = max(1, min(int(os.getenv("REPORT_AGENT_MAX_WORKERS", "3")), len(agents) or 1))

        def run_one(agent: SectionAgent) -> tuple[SectionAgent, SectionState, AgentLog]:
            started = time.perf_counter()
            logger.info("[START] %s", agent.name)
            try:
                section = agent.draft(state)
                duration = time.perf_counter() - started
                log = AgentLog(agent=agent.name, status="completed", duration_seconds=duration)
                logger.info("[DONE] %s %.2fs", agent.name, duration)
                return agent, section, log
            except Exception as error:
                duration = time.perf_counter() - started
                log = AgentLog(agent=agent.name, status="failed", duration_seconds=duration, error=str(error))
                logger.exception("[FAIL] %s %.2fs", agent.name, duration)
                raise RuntimeError(f"{agent.name} failed: {error}") from error

        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="report-agent") as executor:
            futures = [executor.submit(run_one, agent) for agent in agents]
            results = []
            for future in as_completed(futures):
                agent, section, log = future.result()
                results.append((agent, section, log))
                if progress_callback:
                    progress_callback(agent.name, log.status)

        # Merge only after workers finish; ReportState remains single-writer.
        for agent, section, log in results:
            state.apply_agent_update(
                agent.name,
                {f"sections.{agent.heading}": section},
                agent.owns,
            )
            state.agent_logs.append(log)


class ValidationAgent:
    name = "validation_agent"
    owns = {"claims", "validation"}

    def run(self, state: ReportState) -> None:
        sections = [
            ReportSection(**section.model_dump(exclude={"status", "issues", "version"}))
            for section in state.sections.values()
        ]
        claims = validate_claims(
            extract_claims_from_sections(sections, state.evidence),
            state.evidence,
        )
        supported = sum(c.validation_status.value == "SUPPORTED" for c in claims)
        needs_review = sum(c.validation_status.value == "NEEDS_REVIEW" for c in claims)
        unsupported = sum(c.validation_status.value == "UNSUPPORTED" for c in claims)
        validation = {
            "status": "validated",
            "errors": [],
            "warnings": [],
            "supported": supported,
            "needs_review": needs_review,
            "unsupported": unsupported,
        }
        state.apply_agent_update(
            self.name,
            {"claims": claims, "validation": validation},
            self.owns,
        )


class TestingAgent:
    """Deterministic report quality gate after claim validation."""

    name = "testing_agent"
    owns = {"validation"}

    def run(self, state: ReportState, required_sections: list[str]) -> None:
        errors: list[str] = []
        warnings: list[str] = []
        for heading in required_sections:
            section = state.sections.get(heading)
            if section is None:
                errors.append(f"Missing required section: {heading}")
            elif heading != "citations" and not section.paragraphs:
                errors.append(f"Empty section: {heading}")

        known_refs = {f"F{index}" for index in range(len(state.evidence.facts))} | {
            f"C{index}" for index in range(len(state.evidence.chunks))
        }
        for section in state.sections.values():
            for reference in section.fact_ids:
                if reference and reference not in known_refs:
                    errors.append(f"Unresolved evidence reference: {reference}")

        unsupported = state.validation.unsupported
        if unsupported:
            warnings.append(f"{unsupported} claims quarantined as unsupported")

        validation = state.validation.model_copy(
            update={
                "status": (
                    "failed"
                    if errors
                    else "passed_with_warnings" if warnings else "passed"
                ),
                "errors": errors,
                "warnings": warnings,
            }
        )
        state.apply_agent_update(self.name, {"validation": validation}, self.owns)


class ReviewAgent:
    """Translate human comments into targeted, persisted revision tasks."""

    name = "review_agent"
    owns = {"human_review", "revision_tasks", "status"}

    def run(self, state: ReportState, comments: list[dict]) -> None:
        tasks = [
            RevisionTask(
                section=str(comment.get("section", "")),
                issue_type=str(comment.get("issue_type", "general")),
                instruction=str(comment.get("comment", "")),
                claim_id=comment.get("claim_id"),
            )
            for comment in comments
            if comment.get("section") and comment.get("comment")
        ]
        review = state.human_review.model_copy(
            update={"status": "revision_requested", "comments": comments}
        )
        state.apply_agent_update(
            self.name,
            {
                "human_review": review,
                "revision_tasks": tasks,
                "status": "revision_requested",
            },
            self.owns,
        )
