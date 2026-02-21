#!/usr/bin/env python3
"""Stage 1 MCP-style tool server (incubation mock implementation)."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List


class Channel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    WEB_FORM = "web_form"


ROOT = Path(__file__).resolve().parents[2]
TICKETS_PATH = ROOT / "context" / "sample-tickets.json"
EVENT_LOG_PATH = ROOT / "specs" / "mcp-tool-events.json"


def _load_tickets() -> List[Dict]:
    return json.loads(TICKETS_PATH.read_text())


def _append_event(event: Dict) -> None:
    rows = []
    if EVENT_LOG_PATH.exists():
        rows = json.loads(EVENT_LOG_PATH.read_text())
    rows.append(event)
    EVENT_LOG_PATH.write_text(json.dumps(rows, indent=2) + "\n")


def search_knowledge_base(query: str, max_results: int = 5) -> Dict:
    query_l = query.lower()
    tickets = _load_tickets()
    matches = []
    for t in tickets:
        blob = f"{t.get('subject', '')} {t.get('message', '')} {t.get('expected_outcome', '')}".lower()
        if query_l in blob:
            matches.append(
                {
                    "ticket_id": t["ticket_id"],
                    "channel": t["channel"],
                    "subject": t.get("subject", ""),
                    "snippet": t["expected_outcome"][:180],
                }
            )
    if not matches:
        return {"status": "ok", "results": [], "message": "No relevant docs found in incubation KB."}
    return {"status": "ok", "results": matches[:max_results], "message": f"Found {min(len(matches), max_results)} matches."}


def create_ticket(customer_id: str, issue: str, priority: str, channel: Channel) -> Dict:
    ticket_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    event = {
        "type": "create_ticket",
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority,
        "channel": channel.value,
    }
    _append_event(event)
    return {"status": "created", "ticket_id": ticket_id}


def get_customer_history(customer_id: str) -> Dict:
    tickets = _load_tickets()
    history = [t for t in tickets if t["customer_id"] == customer_id]
    return {
        "status": "ok",
        "customer_id": customer_id,
        "interactions_count": len(history),
        "interactions": history,
    }


def escalate_to_human(ticket_id: str, reason: str) -> Dict:
    escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
    event = {
        "type": "escalate_to_human",
        "ticket_id": ticket_id,
        "reason": reason,
        "escalation_id": escalation_id,
    }
    _append_event(event)
    return {"status": "escalated", "escalation_id": escalation_id}


def send_response(ticket_id: str, message: str, channel: Channel) -> Dict:
    if channel == Channel.EMAIL:
        formatted = f"Hello,\n\n{message}\n\nBest regards,\nCustomer Success Team"
    elif channel == Channel.WHATSAPP:
        formatted = message[:180]
    else:
        formatted = message
    event = {
        "type": "send_response",
        "ticket_id": ticket_id,
        "channel": channel.value,
        "message": formatted,
    }
    _append_event(event)
    return {"status": "sent", "ticket_id": ticket_id, "channel": channel.value, "message": formatted}


def list_tools() -> List[Dict]:
    return [
        {"name": "search_knowledge_base", "input": {"query": "str", "max_results": "int"}, "output": "matching snippets"},
        {"name": "create_ticket", "input": {"customer_id": "str", "issue": "str", "priority": "str", "channel": "Channel"}, "output": "ticket_id"},
        {"name": "get_customer_history", "input": {"customer_id": "str"}, "output": "interaction history across channels"},
        {"name": "escalate_to_human", "input": {"ticket_id": "str", "reason": "str"}, "output": "escalation_id"},
        {"name": "send_response", "input": {"ticket_id": "str", "message": "str", "channel": "Channel"}, "output": "delivery status"},
    ]


if __name__ == "__main__":
    print("Stage 1 MCP tool server (mock) ready.")
    print(json.dumps({"tool_count": len(list_tools()), "tools": list_tools()}, indent=2))
