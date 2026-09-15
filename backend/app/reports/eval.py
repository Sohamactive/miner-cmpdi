"""Evaluation harness — golden 20 facts / 20 questions, time-saved, accuracy, automation."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

GOLDEN_FACTS = [
    {"entity": "MCL", "metric": "coal_production", "period": "FY2024-25", "value": 173.6, "unit": "MT"},
    {"entity": "CIL", "metric": "coal_production", "period": "FY2024-25", "value": 703.0, "unit": "MT"},
    {"entity": "CMPDI", "metric": "exploration", "period": "FY2024-25", "value": 12.5, "unit": "million tonnes"},
    {"entity": "MCL", "metric": "overburden", "period": "FY2024-25", "value": 185.0, "unit": "cum million"},
    {"entity": "ECL", "metric": "coal_production", "period": "FY2024-25", "value": 123.0, "unit": "MT"},
    {"entity": "BCCL", "metric": "coal_production", "period": "FY2024-25", "value": 52.0, "unit": "MT"},
    {"entity": "NCL", "metric": "coal_production", "period": "FY2024-25", "value": 89.0, "unit": "MT"},
    {"entity": "SECL", "metric": "coal_production", "period": "FY2024-25", "value": 167.0, "unit": "MT"},
    {"entity": "WCL", "metric": "coal_production", "period": "FY2024-25", "value": 78.0, "unit": "MT"},
    {"entity": "NECL", "metric": "coal_production", "period": "FY2024-25", "value": 4.2, "unit": "MT"},
    {"entity": "CIL", "metric": "despatch", "period": "FY2024-25", "value": 695.0, "unit": "MT"},
    {"entity": "MCL", "metric": "shirting", "period": "FY2024-25", "value": 45.0, "unit": "million cubic meters"},
    {"entity": "CMPDI", "metric": "drilling", "period": "FY2024-25", "value": 250000, "unit": "metres"},
    {"entity": "CIL", "metric": "offtake", "period": "FY2024-25", "value": 690.0, "unit": "MT"},
    {"entity": "MCL", "metric": "financial_turnover", "period": "FY2024-25", "value": 32000, "unit": "crore"},
    {"entity": "CIL", "metric": "annual_report", "period": "FY2023-24", "value": 674.0, "unit": "MT"},
    {"entity": "MCL", "metric": "coal_supply", "period": "FY2024-25", "value": 170.0, "unit": "MT"},
    {"entity": "ECL", "metric": "overburden", "period": "FY2024-25", "value": 95.0, "unit": "cum million"},
    {"entity": "CIL", "metric": "capital_expenditure", "period": "FY2024-25", "value": 18000, "unit": "crore"},
    {"entity": "MCL", "metric": "employee_count", "period": "FY2024-25", "value": 52000, "unit": ""},
]

GOLDEN_QUESTIONS = [
    {"question": "What was MCL coal production in FY2024-25?", "expected_value": 173.6, "expected_unit": "MT"},
    {"question": "What is the total CIL coal production?", "expected_value": 703.0, "expected_unit": "MT"},
    {"question": "How much overburden did MCL remove?", "expected_value": 185.0, "expected_unit": "cum million"},
    {"question": "What was ECL production?", "expected_value": 123.0, "expected_unit": "MT"},
    {"question": "What is BCCL coal production?", "expected_value": 52.0, "expected_unit": "MT"},
    {"question": "How much coal did NCL produce?", "expected_value": 89.0, "expected_unit": "MT"},
    {"question": "What was SECL production?", "expected_value": 167.0, "expected_unit": "MT"},
    {"question": "WCL coal production figures?", "expected_value": 78.0, "expected_unit": "MT"},
    {"question": "What was CIL despatch?", "expected_value": 695.0, "expected_unit": "MT"},
    {"question": "How much drilling did CMPDI do?", "expected_value": 250000, "expected_unit": "metres"},
    {"question": "MCL financial turnover?", "expected_value": 32000, "expected_unit": "crore"},
    {"question": "What was CMPDI exploration volume?", "expected_value": 12.5, "expected_unit": "million tonnes"},
    {"question": "CIL offtake figures?", "expected_value": 690.0, "expected_unit": "MT"},
    {"question": "MCL shirting volume?", "expected_value": 45.0, "expected_unit": "million cubic meters"},
    {"question": "CIL annual report production FY23-24?", "expected_value": 674.0, "expected_unit": "MT"},
    {"question": "MCL coal supply?", "expected_value": 170.0, "expected_unit": "MT"},
    {"question": "ECL overburden removal?", "expected_value": 95.0, "expected_unit": "cum million"},
    {"question": "CIL capital expenditure?", "expected_value": 18000, "expected_unit": "crore"},
    {"question": "How many employees does MCL have?", "expected_value": 52000, "expected_unit": ""},
    {"question": "What was NECL production?", "expected_value": 4.2, "expected_unit": "MT"},
]


def evaluate_facts(retrieved_facts: list[dict]) -> dict:
    """Compare retrieved facts against golden set."""
    matched = 0
    total = len(GOLDEN_FACTS)
    details: list[dict] = []

    for golden in GOLDEN_FACTS:
        found = False
        for fact in retrieved_facts:
            if (fact.get("value") == golden["value"] and
                fact.get("unit") == golden["unit"]):
                found = True
                break
        if found:
            matched += 1
        details.append({"golden": golden, "matched": found})

    accuracy = (matched / total * 100) if total > 0 else 0
    return {"accuracy_pct": round(accuracy, 1), "matched": matched, "total": total, "details": details}


def evaluate_claims(claims: list[dict]) -> dict:
    """Evaluate claim validation results."""
    supported = sum(1 for c in claims if c.get("validation_status") == "SUPPORTED")
    needs_review = sum(1 for c in claims if c.get("validation_status") == "NEEDS_REVIEW")
    unsupported = sum(1 for c in claims if c.get("validation_status") == "UNSUPPORTED")
    total = len(claims)

    support_rate = (supported / total * 100) if total > 0 else 0
    return {
        "support_rate_pct": round(support_rate, 1),
        "supported": supported,
        "needs_review": needs_review,
        "unsupported": unsupported,
        "total": total,
    }


def evaluate_time_saved(manual_seconds: float, ai_seconds: float) -> dict:
    """Calculate time saved percentage."""
    if manual_seconds <= 0:
        return {"time_saved_pct": 0.0, "manual_seconds": manual_seconds, "ai_seconds": ai_seconds}
    saved = (manual_seconds - ai_seconds) / manual_seconds * 100
    return {"time_saved_pct": round(saved, 1), "manual_seconds": manual_seconds, "ai_seconds": ai_seconds}


def evaluate_automation(automated_steps: int, total_steps: int) -> dict:
    """Calculate automation percentage."""
    pct = (automated_steps / total_steps * 100) if total_steps > 0 else 0
    return {"automation_pct": round(pct, 1), "automated": automated_steps, "total": total_steps}


def run_full_evaluation(
    retrieved_facts: list[dict],
    claims: list[dict],
    manual_seconds: float = 0,
    ai_seconds: float = 0,
    automated_steps: int = 0,
    total_steps: int = 0,
) -> dict:
    """Run complete evaluation and return results."""
    results = {
        "fact_accuracy": evaluate_facts(retrieved_facts),
        "claim_validation": evaluate_claims(claims),
        "time_saved": evaluate_time_saved(manual_seconds, ai_seconds),
        "automation": evaluate_automation(automated_steps, total_steps),
    }

    logger.info("Evaluation complete:")
    logger.info("  Fact accuracy: %.1f%%", results["fact_accuracy"]["accuracy_pct"])
    logger.info("  Claim support rate: %.1f%%", results["claim_validation"]["support_rate_pct"])
    logger.info("  Time saved: %.1f%%", results["time_saved"]["time_saved_pct"])
    logger.info("  Automation: %.1f%%", results["automation"]["automation_pct"])

    return results
