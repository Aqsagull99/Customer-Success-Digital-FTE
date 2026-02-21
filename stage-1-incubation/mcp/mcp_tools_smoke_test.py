#!/usr/bin/env python3
"""Smoke test for Stage 1 MCP tools."""

from __future__ import annotations

import json
from pathlib import Path

from customer_success_mcp_server import (  # type: ignore
    Channel,
    create_ticket,
    escalate_to_human,
    get_customer_history,
    list_tools,
    search_knowledge_base,
    send_response,
)


OUT_PATH = Path(__file__).resolve().parents[2] / "specs" / "mcp-smoke-test-report.json"


def main() -> None:
    tools = list_tools()
    assert len(tools) >= 5

    kb = search_knowledge_base("refund", max_results=3)
    created = create_ticket(
        customer_id="smoke@example.com",
        issue="Refund not processed",
        priority="high",
        channel=Channel.EMAIL,
    )
    history = get_customer_history("smoke@example.com")
    escalated = escalate_to_human(created["ticket_id"], "billing dispute in smoke test")
    sent = send_response(created["ticket_id"], "We have escalated your request.", Channel.EMAIL)

    report = {
        "tool_count": len(tools),
        "search_knowledge_base_status": kb["status"],
        "create_ticket_status": created["status"],
        "get_customer_history_interactions": history["interactions_count"],
        "escalate_to_human_status": escalated["status"],
        "send_response_status": sent["status"],
    }
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print("mcp_tools_smoke_test complete")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
