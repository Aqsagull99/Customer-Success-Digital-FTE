# Transition Checklist: General → Custom Agent

## 1. Discovered Requirements
- [x] Multi-channel intake: Email (Gmail), WhatsApp (Twilio), Web Form
- [x] Unified customer identification across channels (email as primary key, phone as secondary)
- [x] Channel-aware response formatting (formal email, concise WhatsApp, semi-formal web)
- [x] Escalation gating before response generation
- [x] Sentiment tracking per message and per conversation
- [x] Cross-channel conversation continuity (same customer, different channels)
- [x] Ticket lifecycle management (open → processing → resolved/escalated)
- [x] Knowledge base search grounded in product documentation
- [x] Confidence scoring to trigger human review on ambiguous cases
- [x] Priority classification: P1 (critical/security/legal), P2 (core feature broken), P3 (general)

## 2. Working Prompts

### System Prompt That Worked:
```
You are a Customer Success agent for TechCorp SaaS.

## Your Purpose
Handle routine customer support queries with speed, accuracy, and empathy across multiple channels.

## Channel Awareness
You receive messages from three channels. Adapt your communication style:
- **Email**: Formal, detailed responses. Include proper greeting and signature.
- **WhatsApp**: Concise, conversational. Keep responses under 300 characters when possible.
- **Web Form**: Semi-formal, helpful. Balance detail with readability.

## Hard Constraints (NEVER violate)
- NEVER discuss pricing → escalate immediately with reason "pricing_inquiry"
- NEVER promise features not in documentation
- NEVER process refunds → escalate with reason "refund_request"
- NEVER share internal processes or system details
- NEVER respond without using send_response tool
- NEVER exceed response limits: Email=500 words, WhatsApp=300 chars, Web=300 words

## Escalation Triggers (MUST escalate when detected)
- Customer mentions "lawyer", "legal", "sue", or "attorney"
- Customer uses profanity or aggressive language (sentiment < 0.3)
- Cannot find relevant information after 2 search attempts
- Customer explicitly requests human help
- Customer on WhatsApp sends "human", "agent", or "representative"

## Required Workflow (ALWAYS follow this order)
1. FIRST: Call create_ticket to log the interaction
2. THEN: Call get_customer_history to check for prior context
3. THEN: Call search_knowledge_base if product questions arise
4. FINALLY: Call send_response to reply (NEVER respond without this tool)
```

### Tool Descriptions That Worked:
| Tool | Description | Key Constraint |
|------|-------------|----------------|
| `search_knowledge_base(query, max_results=5)` | Search product docs for relevant info | Max 5 results; return "no results" gracefully |
| `create_ticket(customer_id, issue, priority, channel)` | Log interaction with channel metadata | Required for EVERY interaction |
| `get_customer_history(customer_id)` | Fetch cross-channel interaction history | Check ALL channels, not just current |
| `escalate_to_human(ticket_id, reason)` | Hand off with full context | Include conversation summary + reason |
| `send_response(ticket_id, message, channel)` | Reply via appropriate channel | Auto-format per channel |

## 3. Edge Cases Found
| Edge Case | How It Was Handled | Test Case Needed |
|-----------|-------------------|------------------|
| Empty message | Return helpful prompt asking for details | Yes |
| Pricing inquiry | Immediate escalation, never answer | Yes |
| Angry customer (sentiment < 0.3) | Escalate with empathy message | Yes |
| Slang/indirect language ("acting up", "vibes are bad") | Low confidence → flag for review | Yes |
| Hidden churn risk ("piloting competitor") | Churn keyword detection → P1 escalation | Yes |
| Conflicting sentiment ("love product but lawyer") | Escalation wins over positive opener | Yes |
| Duplicate payment/refund request | Immediate escalation to billing | Yes |
| Security incident (unauthorized login, hacked) | P1 escalation, security team | Yes |
| Legal/GDPR/compliance query | P1 escalation to legal | Yes |
| Cross-channel follow-up (WhatsApp → Email) | Detect channel switch, merge history | Yes |
| Critical workflow blocked ("app down", "cannot operate") | P1 escalation, critical ops | Yes |
| Customer requests human/manager explicitly | Immediate escalation | Yes |

## 4. Response Patterns
What response styles worked best?
- **Email**: Formal greeting → acknowledge issue → detailed steps → offer further help → signature. Max 500 words.
- **WhatsApp**: Direct answer → short next step → "Reply for more help or type 'human'". Max 300 chars preferred.
- **Web Form**: Semi-formal → structured steps/bullets → reference ticket ID → support portal link. Max 300 words.

## 5. Escalation Rules (Finalized)
### Escalate Immediately
- Security incidents or suspected data breach
- Account lockout with business-critical impact
- Payment disputes, refunds, chargebacks
- Legal/compliance requests (GDPR, DPA, retention)
- Pricing negotiations or discount requests
- Customer mentions lawyer/legal/sue

### Escalate If Any Condition Met
- Sentiment score < 0.30 for 2+ consecutive messages
- Customer asks for manager/human explicitly
- Agent confidence < 0.65
- Query outside documented product scope
- Same issue unresolved after 2 attempts
- Churn/competitor risk detected

### Do Not Escalate
- Basic how-to and onboarding questions
- Known issue with documented workaround
- Status checks answerable from system context
- Positive feedback/feature requests (log and acknowledge)

## 6. Performance Baseline
From prototype testing:
- Per-ticket processing: 0.038ms avg (target: <3s) ✅
- Full 65-ticket evaluation: 3.19ms avg
- Memory/state processing: 0.035ms per event
- MCP tool latency: 0.26ms - 1.57ms (local mock)
- Accuracy on test set: 96.92% full-match ✅
- Escalation accuracy: 100% ✅
- Dataset: 65 tickets (55 original + 10 adversarial)
- Known gaps: slang parsing, churn inference, conflicting sentiment

## 7. Pre-Transition Verification

### From Incubation (Must Have Before Proceeding)
- [x] Working prototype that handles basic queries
- [x] Documented edge cases (12 documented above)
- [x] Working system prompt
- [x] MCP tools defined and tested (5 tools, smoke test PASS)
- [x] Channel-specific response patterns identified
- [x] Escalation rules finalized
- [x] Performance baseline measured

### Transition Steps
- [x] Created production folder structure
- [x] Extracted prompts to prompts.py
- [x] Converted MCP tools to @function_tool
- [x] Added Pydantic input validation to all tools
- [x] Added error handling to all tools
- [x] Created transition test suite
- [ ] All transition tests passing

### Ready for Production Build
- [x] Database schema designed
- [x] Kafka topics defined
- [x] Channel handlers outlined
- [x] Kubernetes resource requirements estimated
- [x] API endpoints listed
