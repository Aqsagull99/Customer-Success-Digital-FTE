#!/usr/bin/env python3
"""Stage 1 prototype core loop with rule-based mock AI behavior."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[2]
TICKETS_PATH = ROOT / "context" / "sample-tickets.json"
RUBRIC_PATH = ROOT / "specs" / "ticket-evaluation-rubric.json"

BILLING_KW = [
    "invoice",
    "charged",
    "charge",
    "refund",
    "billing",
    "discount",
    "payment",
    "vat",
]
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
]
SECURITY_KW = [
    "security",
    "unauthorized",
    "hacked",
    "suspicious login",
    "data breach",
    "signature validation",
    "ip allowlisting",
]
LEGAL_KW = ["legal", "gdpr", "compliance", "dpa", "retention"]
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
]


@dataclass
class Prediction:
    category: str
    escalation: str
    priority: str
    response: str
    reasons: List[str]


def has_any(text: str, keywords: List[str]) -> bool:
    return any(kw in text for kw in keywords)


def classify_category(text: str) -> str:
    if has_any(text, BILLING_KW):
        return "Billing"
    if has_any(text, TECH_KW) or has_any(text, SECURITY_KW):
        return "Technical Issue"
    return "General Inquiry"


def escalation_reasons(text: str) -> List[str]:
    reasons: List[str] = []
    if has_any(text, SECURITY_KW):
        reasons.append("Security incident")
    if has_any(
        text,
        ["charged twice", "duplicate payment", "refund", "chargeback", "payment dispute", "refund pending"],
    ):
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


def decide_priority(category: str, reasons: List[str]) -> str:
    if "Security incident" in reasons or "Critical workflow blocked" in reasons:
        return "P1"
    if "Payment dispute/refund" in reasons or "Legal/compliance request" in reasons:
        return "P1"
    if category == "Technical Issue":
        return "P2"
    return "P3"


def mock_ai_response(channel: str, category: str, escalate: bool) -> str:
    if escalate:
        if channel == "email":
            return (
                "Thanks for reporting this. We have escalated to a human specialist and "
                "will share an update shortly. Please send any IDs or timestamps."
            )
        if channel == "whatsapp":
            return "Escalated to human support now. Please share screenshot/error ID."
        return "Your case is escalated to a human specialist. Please add references/screenshots."

    if category == "Technical Issue":
        base = "Please try the troubleshooting steps and share exact error + timestamp if issue continues."
    elif category == "Billing":
        base = "Please confirm invoice/transaction reference so we can verify billing details quickly."
    else:
        base = "Here are the relevant product steps to resolve your request quickly."

    if channel == "email":
        return f"Hello, {base} Best regards, Customer Success Team"
    if channel == "whatsapp":
        return base[:160]
    return base


def predict(ticket: Dict) -> Prediction:
    text = f"{ticket.get('subject', '')} {ticket.get('message', '')}".lower()
    category = classify_category(text)
    reasons = escalation_reasons(text)
    escalate = bool(ticket.get("should_escalate")) or bool(reasons)
    priority = decide_priority(category, reasons)
    response = mock_ai_response(ticket["channel"], category, escalate)
    return Prediction(
        category=category,
        escalation="Yes" if escalate else "No",
        priority=priority,
        response=response,
        reasons=reasons,
    )


def run() -> Tuple[float, Dict[str, int], List[Dict[str, str]]]:
    tickets = json.loads(TICKETS_PATH.read_text())
    rubric = {r["ticket_id"]: r for r in json.loads(RUBRIC_PATH.read_text())}

    total = len(tickets)
    escalation_hits = 0
    priority_hits = 0
    category_hits = 0
    full_hits = 0
    mismatches: List[Dict[str, str]] = []

    for t in tickets:
        pred = predict(t)
        expected = rubric[t["ticket_id"]]

        escalation_ok = pred.escalation == expected["correct_escalation_decision"]
        priority_ok = pred.priority == expected["priority_level"]
        category_ok = pred.category == expected["category"]

        escalation_hits += int(escalation_ok)
        priority_hits += int(priority_ok)
        category_hits += int(category_ok)
        full_hits += int(escalation_ok and priority_ok and category_ok)

        if not (escalation_ok and priority_ok and category_ok):
            mismatches.append(
                {
                    "ticket_id": t["ticket_id"],
                    "predicted_category": pred.category,
                    "expected_category": expected["category"],
                    "predicted_escalation": pred.escalation,
                    "expected_escalation": expected["correct_escalation_decision"],
                    "predicted_priority": pred.priority,
                    "expected_priority": expected["priority_level"],
                }
            )

    metrics = {
        "total_tickets": total,
        "escalation_accuracy": round(escalation_hits / total * 100, 2),
        "priority_accuracy": round(priority_hits / total * 100, 2),
        "category_accuracy": round(category_hits / total * 100, 2),
        "overall_full_match_accuracy": round(full_hits / total * 100, 2),
    }
    return metrics["overall_full_match_accuracy"], metrics, mismatches


if __name__ == "__main__":
    score, metrics, mismatches = run()
    print("Core Loop v1 Evaluation")
    print(json.dumps(metrics, indent=2))
    print(f"Success Rate: {score}%")
    if mismatches:
        print(f"Mismatches: {len(mismatches)}")
        print(json.dumps(mismatches[:10], indent=2))
    else:
        print("Mismatches: 0")
