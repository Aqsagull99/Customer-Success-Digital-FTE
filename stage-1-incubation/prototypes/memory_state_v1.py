#!/usr/bin/env python3
"""Stage 1 memory/state prototype for cross-channel conversation tracking."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
TICKETS_PATH = ROOT / "context" / "sample-tickets.json"
OUT_PATH = ROOT / "specs" / "memory-state-v1-report.json"

POSITIVE_WORDS = {"love", "great", "thanks", "kind", "helpful", "good"}
NEGATIVE_WORDS = {
    "unacceptable",
    "ridiculous",
    "frustrating",
    "angry",
    "lawsuit",
    "sue",
    "ruined",
    "hacked",
    "down",
}
TOPIC_KEYWORDS = {
    "billing": {"billing", "charged", "refund", "invoice", "payment", "vat"},
    "security": {"security", "hacked", "unauthorized", "signature"},
    "access": {"login", "locked", "password", "access"},
    "reliability": {"outage", "down", "latency", "500", "freeze", "failing"},
    "feature_request": {"feature request", "please add", "need dark mode", "bulk close", "widgets"},
}


@dataclass
class ConversationState:
    customer_id: str
    messages: List[Dict] = field(default_factory=list)
    channels_seen: List[str] = field(default_factory=list)
    channel_switches: int = 0
    sentiment_scores: List[float] = field(default_factory=list)
    topics_counter: Counter = field(default_factory=Counter)
    resolution_status: str = "pending"


def sentiment_score(text: str) -> float:
    tokens = text.lower().split()
    pos = sum(1 for t in tokens if t.strip(".,!?") in POSITIVE_WORDS)
    neg = sum(1 for t in tokens if t.strip(".,!?") in NEGATIVE_WORDS)
    raw = pos - neg
    # Normalize to 0..1 for simple trend tracking.
    return max(0.0, min(1.0, 0.5 + raw * 0.2))


def extract_topics(text: str) -> List[str]:
    text_l = text.lower()
    hits = []
    for topic, kws in TOPIC_KEYWORDS.items():
        if any(k in text_l for k in kws):
            hits.append(topic)
    return hits or ["general"]


def update_state(state: ConversationState, event: Dict) -> None:
    message_text = f"{event.get('subject', '')} {event.get('message', '')}".strip()
    ch = event["channel"]
    if state.channels_seen and state.channels_seen[-1] != ch:
        state.channel_switches += 1
    if not state.channels_seen or state.channels_seen[-1] != ch:
        state.channels_seen.append(ch)

    state.messages.append(
        {
            "ticket_id": event["ticket_id"],
            "channel": ch,
            "message": event["message"],
            "should_escalate": event["should_escalate"],
        }
    )
    state.sentiment_scores.append(sentiment_score(message_text))
    for topic in extract_topics(message_text):
        state.topics_counter[topic] += 1

    if event["should_escalate"]:
        state.resolution_status = "escalated"
    elif state.resolution_status != "escalated":
        state.resolution_status = "solved"


def build_memory_report(events: List[Dict]) -> Dict:
    conversations: Dict[str, ConversationState] = {}
    for e in events:
        cid = e["customer_id"]
        if cid not in conversations:
            conversations[cid] = ConversationState(customer_id=cid)
        update_state(conversations[cid], e)

    # Add a synthetic cross-channel continuation to validate stage-1 requirement.
    synthetic = [
        {
            "ticket_id": "SYN-1",
            "channel": "whatsapp",
            "customer_id": "cross-channel-demo@example.com",
            "subject": "",
            "message": "login still broken from earlier email",
            "should_escalate": False,
        },
        {
            "ticket_id": "SYN-2",
            "channel": "email",
            "customer_id": "cross-channel-demo@example.com",
            "subject": "Follow-up",
            "message": "Issue persists and now dashboard is down",
            "should_escalate": True,
        },
    ]
    for e in synthetic:
        cid = e["customer_id"]
        if cid not in conversations:
            conversations[cid] = ConversationState(customer_id=cid)
        update_state(conversations[cid], e)

    per_customer = {}
    for cid, state in conversations.items():
        avg_sentiment = round(sum(state.sentiment_scores) / len(state.sentiment_scores), 2)
        per_customer[cid] = {
            "message_count": len(state.messages),
            "channels_seen": state.channels_seen,
            "channel_switches": state.channel_switches,
            "avg_sentiment": avg_sentiment,
            "top_topics": [t for t, _ in state.topics_counter.most_common(3)],
            "resolution_status": state.resolution_status,
        }

    report = {
        "total_events_processed": len(events) + len(synthetic),
        "total_customers": len(per_customer),
        "customers_with_channel_switch": sum(1 for x in per_customer.values() if x["channel_switches"] > 0),
        "escalated_customers": sum(1 for x in per_customer.values() if x["resolution_status"] == "escalated"),
        "sample_cross_channel_customer": per_customer.get("cross-channel-demo@example.com", {}),
        "customer_states": per_customer,
    }
    return report


def main() -> None:
    events = json.loads(TICKETS_PATH.read_text())
    report = build_memory_report(events)
    OUT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print("memory_state_v1 complete")
    print(json.dumps({k: report[k] for k in ["total_events_processed", "total_customers", "customers_with_channel_switch", "escalated_customers"]}, indent=2))


if __name__ == "__main__":
    main()
