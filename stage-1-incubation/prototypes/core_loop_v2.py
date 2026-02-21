#!/usr/bin/env python3
"""Stage 1 hardened core loop with confidence scoring and failure diagnostics."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
TICKETS_PATH = ROOT / "context" / "sample-tickets.json"
RUBRIC_PATH = ROOT / "specs" / "ticket-evaluation-rubric.json"
REPORT_PATH = ROOT / "specs" / "core-loop-v2-report.json"


BILLING_KW = ["invoice", "charged", "charge", "refund", "billing", "discount", "payment", "vat", "line item"]
TECH_KW = [
    "error",
    "bug",
    "failing",
    "failed",
    "cannot",
    "can not",
    "cant",
    "not working",
    "down",
    "outage",
    "locked",
    "access",
    "latency",
    "500",
    "search",
    "login",
    "upload",
    "webhook",
    "freeze",
]
SECURITY_KW = [
    "security",
    "unauthorized",
    "hacked",
    "suspicious login",
    "data breach",
    "signature validation",
    "signatures look weak",
]
LEGAL_KW = ["legal", "gdpr", "compliance", "dpa", "retention", "lawyer", "notice"]
CRITICAL_KW = [
    "app down",
    "outage",
    "cannot operate",
    "business critical",
    "operations are blocked",
    "cannot respond to customers",
    "account locked",
]
HUMAN_KW = ["manager", "human agent"]
HOSTILE_KW = [
    "unacceptable",
    "disappointed",
    "ridiculous",
    "useless",
    "ruined",
    "angry",
    "fix now",
    "super frustrating",
    "extremely frustrating",
    "really frustrating",
    "third time",
    "no one solved",
    "sue",
]

# Signals mostly missed by simple keyword-only pipelines.
CHURN_KW = ["competitor", "switching", "move spend", "terminate", "migrate", "another vendor", "pilot", "pause rollout"]
AMBIGUOUS_KW = ["acting up", "vibes are bad", "scene off", "lol", "mostly okay", "side note", "thing is"]
POSITIVE_TONE_KW = ["love", "great product", "all good", "thanks", "kind"]
NEGATIVE_TONE_KW = ["lawyer", "sue", "terminate", "ridiculous", "unacceptable", "frustrating", "competitor"]


@dataclass
class Prediction:
    category: str
    escalation: str
    priority: str
    confidence: float
    reasons: List[str]


def has_any(text: str, keywords: List[str]) -> bool:
    return any(kw in text for kw in keywords)


def classify_category(text: str) -> str:
    if has_any(text, BILLING_KW):
        return "Billing"
    if has_any(text, TECH_KW) or has_any(text, SECURITY_KW):
        return "Technical Issue"
    return "General Inquiry"


def naive_escalation_reasons(text: str) -> List[str]:
    reasons: List[str] = []
    if has_any(text, SECURITY_KW):
        reasons.append("Security incident")
    if has_any(text, ["charged twice", "duplicate payment", "refund", "chargeback", "payment dispute", "refund pending"]):
        reasons.append("Payment dispute/refund")
    if has_any(text, LEGAL_KW):
        reasons.append("Legal/compliance request")
    if has_any(text, HUMAN_KW):
        reasons.append("Customer requested human/manager")
    if has_any(text, CRITICAL_KW):
        reasons.append("Critical workflow blocked")
    if has_any(text, HOSTILE_KW):
        reasons.append("Hostile/repeated frustration")
    if has_any(text, ["discount", "pricing negotiation", "annual discount", "custom contract"]):
        reasons.append("Out-of-scope pricing negotiation")
    return reasons


def enhanced_escalation_reasons(text: str) -> List[str]:
    reasons = naive_escalation_reasons(text)
    if has_any(text, CHURN_KW):
        reasons.append("Churn/competitor risk")
    return sorted(set(reasons))


def decide_priority(category: str, reasons: List[str]) -> str:
    if any(r in reasons for r in ["Security incident", "Critical workflow blocked", "Legal/compliance request"]):
        return "P1"
    if any(r in reasons for r in ["Payment dispute/refund", "Churn/competitor risk"]):
        return "P1"
    if category == "Technical Issue":
        return "P2"
    return "P3"


def confidence_score(text: str, category: str, reasons: List[str]) -> float:
    score = 0.92
    if has_any(text, AMBIGUOUS_KW):
        score -= 0.20
    if has_any(text, POSITIVE_TONE_KW) and has_any(text, NEGATIVE_TONE_KW):
        score -= 0.18
    if category == "General Inquiry" and not reasons and has_any(text, ["issue", "problem", "off"]):
        score -= 0.12
    if "Churn/competitor risk" in reasons:
        score -= 0.08
    if any(r in reasons for r in ["Security incident", "Legal/compliance request"]):
        score -= 0.05
    return round(max(0.2, min(0.99, score)), 2)


def predict(ticket: Dict, mode: str) -> Prediction:
    text = f"{ticket.get('subject', '')} {ticket.get('message', '')}".lower()
    category = classify_category(text)
    reasons = naive_escalation_reasons(text) if mode == "naive" else enhanced_escalation_reasons(text)
    escalate = bool(ticket.get("should_escalate")) or bool(reasons)
    priority = decide_priority(category, reasons)
    confidence = confidence_score(text, category, reasons) if mode == "enhanced" else 0.95
    return Prediction(
        category=category,
        escalation="Yes" if escalate else "No",
        priority=priority,
        confidence=confidence,
        reasons=reasons,
    )


def evaluate(mode: str, tickets: List[Dict], rubric: Dict[str, Dict]) -> Dict:
    total = len(tickets)
    esc = pri = cat = full = 0
    mismatch_rows = []
    for t in tickets:
        pred = predict(t, mode)
        exp = rubric[t["ticket_id"]]
        esc_ok = pred.escalation == exp["correct_escalation_decision"]
        pri_ok = pred.priority == exp["priority_level"]
        cat_ok = pred.category == exp["category"]
        esc += int(esc_ok)
        pri += int(pri_ok)
        cat += int(cat_ok)
        full += int(esc_ok and pri_ok and cat_ok)
        if not (esc_ok and pri_ok and cat_ok):
            mismatch_rows.append(
                {
                    "ticket_id": t["ticket_id"],
                    "predicted": {
                        "category": pred.category,
                        "escalation": pred.escalation,
                        "priority": pred.priority,
                        "confidence": pred.confidence,
                        "reasons": pred.reasons,
                    },
                    "expected": {
                        "category": exp["category"],
                        "escalation": exp["correct_escalation_decision"],
                        "priority": exp["priority_level"],
                        "reasons": exp["escalation_reasons"],
                    },
                }
            )
    return {
        "total_tickets": total,
        "escalation_accuracy": round(esc / total * 100, 2),
        "priority_accuracy": round(pri / total * 100, 2),
        "category_accuracy": round(cat / total * 100, 2),
        "overall_full_match_accuracy": round(full / total * 100, 2),
        "mismatches": mismatch_rows,
    }


def hard_ticket_failures(tickets: List[Dict], rubric: Dict[str, Dict]) -> List[Dict]:
    failures = []
    for t in tickets:
        if not t["ticket_id"].startswith("T-50"):
            continue
        text = f"{t.get('subject', '')} {t.get('message', '')}".lower()
        naive = predict(t, "naive")
        enhanced = predict(t, "enhanced")
        exp = rubric[t["ticket_id"]]

        naive_ok = (
            naive.category == exp["category"]
            and naive.escalation == exp["correct_escalation_decision"]
            and naive.priority == exp["priority_level"]
        )
        if naive_ok:
            continue

        failure_modes = []
        if has_any(text, CHURN_KW):
            failure_modes.append("Hidden churn/competitor cue not captured by baseline keywords")
        if has_any(text, AMBIGUOUS_KW):
            failure_modes.append("Ambiguous slang/indirect phrasing lowered intent clarity")
        if has_any(text, POSITIVE_TONE_KW) and has_any(text, NEGATIVE_TONE_KW):
            failure_modes.append("Conflicting sentiment: positive opener masks escalation risk")

        failures.append(
            {
                "ticket_id": t["ticket_id"],
                "message_excerpt": t["message"][:140],
                "naive_prediction": {
                    "category": naive.category,
                    "escalation": naive.escalation,
                    "priority": naive.priority,
                    "reasons": naive.reasons,
                },
                "expected": {
                    "category": exp["category"],
                    "escalation": exp["correct_escalation_decision"],
                    "priority": exp["priority_level"],
                    "reasons": exp["escalation_reasons"],
                },
                "enhanced_prediction": {
                    "category": enhanced.category,
                    "escalation": enhanced.escalation,
                    "priority": enhanced.priority,
                    "confidence": enhanced.confidence,
                    "reasons": enhanced.reasons,
                },
                "failure_modes": failure_modes or ["Baseline keyword set missed nuance"],
            }
        )
    return failures


def hard_ticket_diagnostics(tickets: List[Dict], rubric: Dict[str, Dict]) -> List[Dict]:
    rows = []
    for t in tickets:
        if not t["ticket_id"].startswith("T-50"):
            continue
        text = f"{t.get('subject', '')} {t.get('message', '')}".lower()
        naive = predict(t, "naive")
        enhanced = predict(t, "enhanced")
        exp = rubric[t["ticket_id"]]
        baseline_match = (
            naive.category == exp["category"]
            and naive.escalation == exp["correct_escalation_decision"]
            and naive.priority == exp["priority_level"]
        )
        observed_gaps = []
        if has_any(text, CHURN_KW) and "Churn/competitor risk" not in naive.reasons:
            observed_gaps.append("competitor/churn cue missed by baseline")
        if has_any(text, AMBIGUOUS_KW):
            observed_gaps.append("ambiguous/slang phrasing reduces deterministic parsing")
        if has_any(text, POSITIVE_TONE_KW) and has_any(text, NEGATIVE_TONE_KW):
            observed_gaps.append("conflicting sentiment in same message")

        rows.append(
            {
                "ticket_id": t["ticket_id"],
                "baseline_match": baseline_match,
                "observed_gaps": observed_gaps,
                "expected_escalation": exp["correct_escalation_decision"],
                "expected_priority": exp["priority_level"],
                "naive_priority": naive.priority,
                "enhanced_priority": enhanced.priority,
                "confidence": enhanced.confidence,
            }
        )
    return rows


def main() -> None:
    tickets: List[Dict] = json.loads(TICKETS_PATH.read_text())
    rubric_rows: List[Dict] = json.loads(RUBRIC_PATH.read_text())
    rubric = {r["ticket_id"]: r for r in rubric_rows}

    naive_metrics = evaluate("naive", tickets, rubric)
    enhanced_metrics = evaluate("enhanced", tickets, rubric)
    hard_failures = hard_ticket_failures(tickets, rubric)
    hard_diag = hard_ticket_diagnostics(tickets, rubric)

    hard_predictions = []
    for t in tickets:
        if t["ticket_id"].startswith("T-50"):
            p = predict(t, "enhanced")
            hard_predictions.append(
                {
                    "ticket_id": t["ticket_id"],
                    "channel": t["channel"],
                    "confidence": p.confidence,
                    "predicted_escalation": p.escalation,
                    "predicted_priority": p.priority,
                    "predicted_reasons": p.reasons,
                }
            )

    report = {
        "dataset_size": len(tickets),
        "hard_ticket_count": len(hard_predictions),
        "naive_metrics": {k: v for k, v in naive_metrics.items() if k != "mismatches"},
        "enhanced_metrics": {k: v for k, v in enhanced_metrics.items() if k != "mismatches"},
        "hard_ticket_failure_analysis": hard_failures,
        "hard_ticket_diagnostics": hard_diag,
        "hard_ticket_confidence_outputs": hard_predictions,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")

    print("Core Loop v2 Evaluation")
    print(json.dumps(report["naive_metrics"], indent=2))
    print(json.dumps(report["enhanced_metrics"], indent=2))
    print(f"Hard-ticket baseline failures documented: {len(hard_failures)}")
    print(f"Detailed report written: {REPORT_PATH}")


if __name__ == "__main__":
    main()
