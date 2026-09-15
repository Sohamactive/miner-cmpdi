"""Review workflow: approve/edit/reject per claim and report sign-off."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.extraction.models import ClaimRecord, Report, ReviewDecision


def approve_claim(session: Session, *, report_id: int, claim_id: int, note: str = "") -> ReviewDecision:
    claim = session.get(ClaimRecord, claim_id)
    if claim is None or claim.report_id != report_id:
        raise ValueError(f"Claim {claim_id} not found in report {report_id}")
    decision = ReviewDecision(report_id=report_id, claim_id=claim_id, action="APPROVE", reviewer_note=note)
    session.add(decision)
    session.commit()
    return decision


def edit_claim(session: Session, *, report_id: int, claim_id: int, edited_text: str, note: str = "") -> ReviewDecision:
    claim = session.get(ClaimRecord, claim_id)
    if claim is None or claim.report_id != report_id:
        raise ValueError(f"Claim {claim_id} not found in report {report_id}")
    claim.claim_text = edited_text
    decision = ReviewDecision(
        report_id=report_id, claim_id=claim_id, action="EDIT",
        reviewer_note=note, edited_text=edited_text,
    )
    session.add(decision)
    session.commit()
    return decision


def reject_claim(session: Session, *, report_id: int, claim_id: int, note: str = "") -> ReviewDecision:
    claim = session.get(ClaimRecord, claim_id)
    if claim is None or claim.report_id != report_id:
        raise ValueError(f"Claim {claim_id} not found in report {report_id}")
    claim.validation_status = "UNSUPPORTED"
    decision = ReviewDecision(report_id=report_id, claim_id=claim_id, action="REJECT", reviewer_note=note)
    session.add(decision)
    session.commit()
    return decision


def approve_report(session: Session, *, report_id: int, note: str = "") -> Report:
    report = session.get(Report, report_id)
    if report is None:
        raise ValueError(f"Report {report_id} not found")
    report.status = "approved"
    decision = ReviewDecision(report_id=report_id, action="APPROVE", reviewer_note=note)
    session.add(decision)
    session.commit()
    return report


def get_review_history(session: Session, *, report_id: int) -> list[ReviewDecision]:
    return list(session.scalars(
        select(ReviewDecision).where(ReviewDecision.report_id == report_id)
    ))
