# Customer Success FTE - Stage 1 Skills

## Overview
This skill set defines the five core capabilities of the Customer Success Digital FTE, discovered and prototyped during Stage 1 (Incubation Phase) of Hackathon 5.

## Skills

### 1. Knowledge Retrieval
- **Trigger:** Customer asks a product question
- **Action:** Search product documentation and resolved ticket history
- **Output:** Up to 5 ranked documentation snippets
- **Fallback:** Escalate if no results after 2 search attempts
- **MCP Tool:** `search_knowledge_base(query, max_results=5)`

### 2. Sentiment Analysis
- **Trigger:** Every incoming customer message
- **Action:** Score message sentiment (0.0 = very negative, 1.0 = very positive)
- **Output:** Sentiment score + confidence level
- **Escalation:** Auto-escalate when sentiment < 0.3
- **Stage 1 Method:** Heuristic keyword matching (Stage 2 upgrades to LLM-based)

### 3. Escalation Decision
- **Trigger:** After response generation, before sending
- **Action:** Evaluate whether the ticket should be handed to a human
- **Inputs:** Conversation context, sentiment trend, ticket category
- **Output:** `should_escalate` (bool) + `reason` code
- **Escalation triggers:**
  - Pricing inquiries
  - Refund requests
  - Legal/compliance questions
  - Hostile sentiment (< 0.3)
  - Security incidents (unauthorized access, hacked account)
  - Explicit human/agent request
  - Critical workflow blocked

### 4. Channel Adaptation
- **Trigger:** Before sending any response
- **Action:** Format response for the target channel
- **Channel constraints:**
  | Channel | Style | Max Length |
  |---------|-------|-----------|
  | Email | Formal, detailed with greeting/signature | 500 words |
  | WhatsApp | Conversational, concise | 300 chars preferred |
  | Web Form | Semi-formal, structured steps | 300 words |
- **Templates:** `specs/channel-response-templates.md`
- **MCP Tool:** `send_response(ticket_id, message, channel)`

### 5. Customer Identification
- **Trigger:** On every incoming message
- **Action:** Identify or create unified customer record
- **Primary key:** Email address
- **Secondary key:** Phone number
- **Output:** Unified `customer_id` + merged cross-channel history
- **Target accuracy:** >95% cross-channel identification
- **MCP Tool:** `get_customer_history(customer_id)`

## MCP Tools (5)
| Tool | Purpose |
|------|---------|
| `search_knowledge_base` | Find relevant product documentation |
| `create_ticket` | Log customer interactions with channel metadata |
| `get_customer_history` | Fetch cross-channel interaction history |
| `escalate_to_human` | Hand off to human with full context |
| `send_response` | Reply via appropriate channel with formatting |

## Stage 1 Performance Baseline
- Escalation accuracy: 100%
- Priority accuracy: 96.92% (after hardening with 10 adversarial tickets)
- Category accuracy: 98.46%
- Full-match accuracy: 96.92%
- Dataset: 65 tickets (55 original + 10 hard cases)

## Known Gaps (for Stage 2)
1. Semantic understanding - rule engine misses indirect language and slang
2. Churn/threat inference - polite churn threats under-prioritized
3. Sentiment modeling - conflicting signals hard to parse with keywords
4. Confidence calibration - heuristic, needs model-driven signals
5. Response quality - template-driven, needs real KB retrieval + memory

## References
- `specs/customer-success-fte-spec.md` - Crystallized specification
- `specs/discovery-log.md` - Full exploration and iteration log
- `specs/channel-response-templates.md` - Channel formatting templates
- `stage-1-incubation/prototypes/` - Working prototype code
- `stage-1-incubation/mcp/` - MCP server and smoke tests
