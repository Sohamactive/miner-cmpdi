"""Reports API — thin HTTP routes per 03_ARCHITECTURE.md."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from threading import Event, Lock, Thread

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from app.extraction.postgres import create_session, create_schema
from app.extraction.models import ClaimRecord, Report, ReportJob

router = APIRouter()

jobs: dict[str, dict] = {}
jobs_lock = Lock()

PIPELINE_STEPS = [
    "Gathering evidence",
    "Drafting sections",
    "Validating claims",
    "Assembling report",
    "Done",
]


class GenerateRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question the report must answer")
    report_type: str = "parliamentary_reply"
    custom_sections: list[str] | None = None
    doc_ids: list[str] = Field(default_factory=list)
    title: str = ""


class FeedbackRequest(BaseModel):
    note: str = ""
    edited_sections: list[dict] | None = None


class ReviewRequest(BaseModel):
    action: str = "APPROVE"  # APPROVE / EDIT / REJECT
    claim_id: int | None = None
    note: str = ""
    edited_text: str | None = None


class ReviewSubmission(BaseModel):
    comments: list[dict] = Field(default_factory=list)


def _set_job_state(job_id: str, **updates) -> None:
    with jobs_lock:
        if job_id not in jobs:
            return
        jobs[job_id].update(updates)
        jobs[job_id]["updated_at"] = time.time()


def _pipeline_progress(step_index: int) -> int:
    bounded = max(0, min(step_index, len(PIPELINE_STEPS) - 1))
    return int((bounded / (len(PIPELINE_STEPS) - 1)) * 100)


def _report_links(report_id: int) -> dict[str, str]:
    return {
        "report_url": f"/api/reports/{report_id}",
        "approve_url": f"/api/reports/{report_id}/approve",
        "download_url": f"/api/reports/{report_id}/download.docx",
    }


@router.post("/generate")
def generate_report(data: GenerateRequest) -> JSONResponse:
    """Generate a report and return its complete structured result in Swagger."""
    from app.reports.pipeline import ReportPipeline

    result = ReportPipeline().run(
        question=data.question,
        report_type=data.report_type,
        custom_sections=data.custom_sections,
        doc_ids=data.doc_ids,
        title=data.title,
    )
    result.update(_report_links(result["report_id"]))
    return JSONResponse(result)


@router.post("/generate-job")
async def generate_report_job(data: GenerateRequest) -> JSONResponse:
    job_id = uuid.uuid4().hex
    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "step_index": 0,
            "step_label": PIPELINE_STEPS[0],
            "progress": 0,
            "error": None,
            "result": None,
            "request": data.model_dump(),
            "created_at": time.time(),
            "updated_at": time.time(),
        }

    def _run():
        try:
            _set_job_state(job_id, status="running", step_index=0, step_label=PIPELINE_STEPS[0], progress=0)
            from app.reports.pipeline import ReportPipeline
            pipeline = ReportPipeline()

            def on_progress(step_index: int, step_label: str) -> None:
                _set_job_state(job_id, step_index=step_index, step_label=step_label, progress=_pipeline_progress(step_index))

            result = pipeline.run(
                question=data.question,
                report_type=data.report_type,
                custom_sections=data.custom_sections,
                doc_ids=data.doc_ids,
                title=data.title,
                progress_callback=on_progress,
            )
            result.update(_report_links(result["report_id"]))
            _set_job_state(job_id, status="needs_review", step_index=4, step_label=PIPELINE_STEPS[4], progress=100, result=result)
        except Exception as exc:
            _set_job_state(job_id, status="failed", error=str(exc))

    worker = Thread(target=_run, daemon=True)
    worker.start()
    return JSONResponse({"job_id": job_id, "status_url": f"/api/reports/job/{job_id}"})


@router.get("/job/{job_id}")
async def get_report_job(job_id: str) -> JSONResponse:
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JSONResponse({
        "job_id": job["job_id"],
        "status": job["status"],
        "step_index": job["step_index"],
        "step_label": job["step_label"],
        "progress": job["progress"],
        "error": job["error"],
        "result": job["result"],
        "created_at": job.get("created_at"),
        "updated_at": job.get("updated_at"),
    })


@router.get("/{report_id}/state")
async def get_report_state(report_id: int) -> JSONResponse:
    """Return versioned agent state persisted with a generated report."""
    session = create_session()
    try:
        report = session.get(Report, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        parameters = json.loads(report.parameters_json or "{}")
        state = parameters.get("report_state")
        if state is None:
            raise HTTPException(status_code=404, detail="Report state not available")
        return JSONResponse(state)
    finally:
        session.close()


@router.post("/{report_id}/review")
async def submit_report_review(report_id: int, data: ReviewSubmission) -> JSONResponse:
    """Store structured human comments and create targeted revision tasks."""
    from app.reports.agents import ReviewAgent
    from app.reports.state import ReportState

    session = create_session()
    try:
        report = session.get(Report, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        parameters = json.loads(report.parameters_json or "{}")
        state_data = parameters.get("report_state")
        if state_data is None:
            raise HTTPException(status_code=409, detail="Report has no agent state")
        state = ReportState.model_validate(state_data)
        ReviewAgent().run(state, data.comments)
        state.report_id = report_id
        report.status = "revision_requested"
        report.parameters_json = json.dumps({
            **parameters,
            "report_state": state.model_dump(mode="json"),
        })
        session.commit()
        return JSONResponse({
            "report_id": report_id,
            "status": report.status,
            "revision_tasks": [task.model_dump() for task in state.revision_tasks],
            "state_url": f"/api/reports/{report_id}/state",
        })
    finally:
        session.close()


@router.get("/{report_id}")
async def get_report(report_id: int) -> JSONResponse:
    session = create_session()
    try:
        report = session.get(Report, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        claims = session.scalars(
            __import__("sqlalchemy").select(ClaimRecord).where(ClaimRecord.report_id == report_id)
        ).all()
        return JSONResponse({
            "id": report.id,
            "report_type": report.report_type,
            "status": report.status,
            "title": report.title,
            "sections": json.loads(report.sections_json or "[]"),
            "claims": [
                {
                    "id": c.id,
                    "claim_text": c.claim_text,
                    "evidence_text": c.evidence_text,
                    "value": c.value,
                    "unit": c.unit,
                    "validation_status": c.validation_status,
                    "confidence": c.confidence,
                }
                for c in claims
            ],
            "version": report.version,
            "created_at": str(report.created_at),
        })
    finally:
        session.close()


@router.get("/{report_id}/claims")
async def get_report_claims(report_id: int) -> JSONResponse:
    session = create_session()
    try:
        claims = session.scalars(
            __import__("sqlalchemy").select(ClaimRecord).where(ClaimRecord.report_id == report_id)
        ).all()
        return JSONResponse([
            {
                "id": c.id,
                "claim_text": c.claim_text,
                "evidence_text": c.evidence_text,
                "value": c.value,
                "unit": c.unit,
                "validation_status": c.validation_status,
                "validation_reasons": json.loads(c.validation_reasons or "[]"),
                "confidence": c.confidence,
            }
            for c in claims
        ])
    finally:
        session.close()


@router.post("/{report_id}/feedback")
async def submit_feedback(report_id: int, data: FeedbackRequest) -> JSONResponse:
    session = create_session()
    try:
        report = session.get(Report, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        from app.reports.pipeline import ReportPipeline
        pipeline = ReportPipeline()
        result = pipeline.revise(
            report_id=report_id,
            feedback_note=data.note,
            edited_sections=data.edited_sections,
        )
        return JSONResponse(result)
    finally:
        session.close()


@router.post("/{report_id}/approve")
async def approve_report(report_id: int, data: ReviewRequest) -> JSONResponse:
    session = create_session()
    try:
        from app.review.service import approve_report as do_approve
        try:
            report = do_approve(session, report_id=report_id, note=data.note)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return JSONResponse({"id": report.id, "status": report.status})
    finally:
        session.close()


@router.get("/{report_id}/download.docx")
async def download_report(report_id: int) -> FileResponse:
    session = create_session()
    try:
        report = session.get(Report, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found")
        if report.status not in ("approved", "exported"):
            raise HTTPException(status_code=400, detail="Report must be approved before download")
        from app.reports.exporter import export_docx
        path = export_docx(report_id=report_id)
        report.status = "exported"
        session.commit()
        return FileResponse(
            path=path,
            filename=f"report-{report_id}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    finally:
        session.close()
