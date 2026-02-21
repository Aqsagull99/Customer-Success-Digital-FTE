# Customer Success FTE Specification

## Purpose
Handle routine customer support queries with speed and consistency across email, WhatsApp, and web form channels.

## Supported Channels
| Channel | Identifier | Response Style | Max Length |
|---|---|---|---|
| Email (Gmail) | Email address | Formal, detailed | 500 words |
| WhatsApp | Phone number | Conversational, concise | 160 chars preferred |
| Web Form | Email address | Semi-formal | 300 words |

## Scope
### In Scope
- Product feature questions
- How-to guidance
- Bug report intake
- Feedback collection
- Cross-channel conversation continuity

### Out of Scope (Escalate)
- Pricing negotiations
- Refund requests
- Legal/compliance questions
- Angry customers (sentiment < 0.3)

## Tools
| Tool | Purpose | Constraints |
|---|---|---|
| search_knowledge_base | Find relevant docs | Max 5 results |
| create_ticket | Log interactions | Required for all conversations; include channel |
| get_customer_history | Fetch past interactions | Must include cross-channel history |
| escalate_to_human | Hand off complex issues | Include summary + reason |
| send_response | Reply to customer | Must apply channel formatting |

## Performance Requirements
- Response time: <3s processing, <30s delivery
- Accuracy: >85% on evaluation set
- Escalation rate: <20% for in-scope queries
- Cross-channel identification: >95%

## Stage 1 Performance Baseline (Measured)
- Per-ticket processing: 0.038ms (well within <3s target)
- Full 65-ticket eval: 3.19ms
- Memory/state per-event: 0.035ms
- MCP tool latency: 0.26-1.57ms (local mock)
- Escalation accuracy: 100.0%
- Priority accuracy: 96.92%
- Category accuracy: 98.46%
- Full-match accuracy: 96.92%
- Note: Stage 1 is heuristic-only (no LLM). Stage 2 will add LLM inference and network latency.
- Full report: `specs/performance-baseline-report.json`

## Guardrails
- Never discuss competitors
- Never provide legal advice
- Never commit discounts or pricing changes
- Escalate when confidence is low

## Open Decisions
- Confidence threshold for escalation:
- P1/P2/P3 exact definitions:
- Maximum retries before escalation:
