# Discovery Log (Stage 1)

## Session Metadata
- Date: 2026-02-19
- Iteration: Stage 1, Exercise 1.1 (Initial Exploration)
- Focus area: Multi-channel ticket analysis, category mapping, tone differences, and escalation decisions

## Input Reviewed
- `context/company-profile.md`
- `context/product-docs.md`
- `context/sample-tickets.json`
- `context/escalation-rules.md`
- `The CRM Digital FTE Factory Final Hackathon 5.md` (Stage 1 requirements, channel-aware discovery expectations)

## Dataset Validation
- Total tickets: 55
- Channel split:
  - Email (Gmail): 20
  - WhatsApp: 20
  - Web Form: 15
- Angry/negative sentiment tickets: 10
  - `T-2003`, `T-2010`, `T-2018`, `T-3002`, `T-3005`, `T-3007`, `T-3010`, `T-3014`, `T-3016`, `T-4006`

## Ticket Categorization (All 55)

### General Inquiry (24)
`T-2001`, `T-2004`, `T-2005`, `T-2009`, `T-2012`, `T-2016`, `T-2017`, `T-2020`, `T-3003`, `T-3004`, `T-3007`, `T-3008`, `T-3009`, `T-3012`, `T-3015`, `T-3016`, `T-3019`, `T-3020`, `T-4003`, `T-4004`, `T-4007`, `T-4009`, `T-4011`, `T-4013`

### Technical Issue (19)
`T-2003`, `T-2007`, `T-2008`, `T-2010`, `T-2011`, `T-2014`, `T-2015`, `T-2019`, `T-3001`, `T-3005`, `T-3011`, `T-3013`, `T-3018`, `T-4001`, `T-4005`, `T-4006`, `T-4010`, `T-4014`, `T-4015`

### Billing (12)
`T-2002`, `T-2006`, `T-2013`, `T-2018`, `T-3002`, `T-3006`, `T-3010`, `T-3014`, `T-3017`, `T-4002`, `T-4008`, `T-4012`

### Escalation Required (34)
Escalation-required signals came from either explicit `should_escalate=true` or rule-based triggers in `context/escalation-rules.md`:
- Payment/refund disputes
- Security risk indicators
- Legal/compliance queries
- Explicit human/manager request
- Critical workflow blocked
- Repeated hostile/frustrated sentiment

## High-Frequency Patterns (Top 3)
1. Billing and refund disputes (12 tickets)
2. Reliability/bug issues (12 tickets)
3. How-to guidance and operational setup questions (9 tickets)

## Refined Tone Gap Analysis

### WhatsApp vs Gmail
- Message length:
  - WhatsApp: short, compressed, low-context, urgency-first
  - Gmail: longer, contextual, structured issue narrative
- Language style:
  - WhatsApp: informal and direct ("fix now", "not working")
  - Gmail: formal and procedural ("please advise", "kindly review")
- Emotional signal:
  - WhatsApp carries sharper emotional spikes in fewer words
  - Gmail includes dissatisfaction but often with explicit detail and history
- Expected response format:
  - WhatsApp expects quick triage + short next step
  - Gmail expects complete explanation + clear follow-up path

### Web Form behavior (added insight)
- More structured problem statements than WhatsApp
- Often includes business impact and explicit request type (refund, legal, manager escalation)
- Suitable for semiformat, checklist-style responses

## Top 10 MUST-Escalate Tickets (Rule-Based)
1. `T-2019` (Email): suspected unauthorized login  
Reason: security incident indicator
2. `T-3018` (WhatsApp): possible hacked account  
Reason: security incident indicator
3. `T-4005` (Web Form): critical dashboard outage blocking operations  
Reason: critical workflow blocked
4. `T-2015` (Email): admin account lockout marked business critical  
Reason: critical workflow blocked
5. `T-4014` (Web Form): persistent account access failure impacting customer response operations  
Reason: unresolved critical workflow block
6. `T-2006` (Email): charged twice, refund requested  
Reason: payment dispute/refund
7. `T-2018` (Email): refund not processed + strong negative sentiment  
Reason: payment dispute/refund plus hostile escalation risk
8. `T-3002` (WhatsApp): duplicate charge + urgent hostile demand  
Reason: payment dispute/refund plus hostile escalation risk
9. `T-4002` (Web Form): duplicate payment refund request  
Reason: payment dispute/refund
10. `T-2009` (Email): GDPR/legal retention confirmation request  
Reason: legal/compliance query

## Stage-1 Discovery Outcomes
- Channel-specific behavior is clear enough to define separate response templates.
- Escalation policy must be strict for billing, security, legal/compliance, and hostile unresolved cases.
- Core loop should prioritize fast intent detection, sentiment signals, and escalation gating before response generation.

## Action Items for Python Core Loop Preparation
1. Implement intent classification for `general`, `technical`, `billing`, `escalation`.
2. Add channel-aware response adapter (`email`, `whatsapp`, `web_form`) with length constraints.
3. Add escalation decision function directly aligned to `context/escalation-rules.md`.
4. Validate with this 55-ticket dataset as baseline test set.

## Exercise 1.2 Execution Log (Core Loop v1)
- Rubric generated: `specs/ticket-evaluation-rubric.json` (55/55 tickets)
- Prototype script created: `stage-1-incubation/prototypes/core_loop_v1.py`
- Evaluation command run:
  - `python3 stage-1-incubation/prototypes/core_loop_v1.py`

### Core Loop v1 Results
- Total tickets evaluated: 55
- Escalation accuracy: 100.0%
- Priority accuracy: 100.0%
- Category accuracy: 100.0%
- Overall full-match accuracy: 100.0%
- Mismatches: 0

### Interpretation
- The baseline rule-based prototype correctly matches the current rubric for all tickets.
- This score is expectedly optimistic because rubric labels and prototype logic are aligned to the same rule set.
- Next iteration should harden evaluation by:
  - Adding paraphrased/ambiguous ticket variants
  - Adding contradictory signals in messages
  - Introducing unseen wording to test generalization

## Exercise 1.2 Hardening Pass (Core Loop v2)
- Added 10 hard tickets to `context/sample-tickets.json` (new total: 65)
  - `T-5001` to `T-5010`
  - Includes conflicting intent, ambiguous/slang phrasing, hidden escalation (competitor/churn risk)
- Regenerated rubric for all 65 tickets: `specs/ticket-evaluation-rubric.json`
- Hardened prototype created: `stage-1-incubation/prototypes/core_loop_v2.py`
- Diagnostic report generated: `specs/core-loop-v2-report.json`

### Metrics: Baseline vs Hardened
- Baseline (`naive` keyword-only):
  - Escalation accuracy: 100.0%
  - Priority accuracy: 92.31%
  - Category accuracy: 98.46%
  - Full-match accuracy: 92.31%
- Hardened (`enhanced` + confidence + churn cues):
  - Escalation accuracy: 100.0%
  - Priority accuracy: 96.92%
  - Category accuracy: 98.46%
  - Full-match accuracy: 96.92%

### Hard Ticket Failure Mapping (10/10 audited)
- Baseline pass: 5
- Baseline fail: 5
- Exact baseline failures:
  1. `T-5002`: slang phrase ("acting up") parsed as general inquiry instead of technical issue (P3 vs expected P2)
  2. `T-5003`: hidden competitor-pilot churn signal missed for priority (P3 vs expected P1)
  3. `T-5005`: casual billing dispute ("charged us extra lol") missed payment-dispute priority uplift (P3 vs expected P1)
  4. `T-5007`: polite wording masked termination/migration threat; churn priority missed (P3 vs expected P1)
  5. `T-5009`: polite invoice question plus vendor-switch threat under-prioritized (P3 vs expected P1)

### Confidence Score Behavior (Hard Set)
- Confidence range: 0.64 to 0.92
- Average confidence: 0.74
- Lowest confidence seen where language was ambiguous or conflicting in tone
- Intended use: trigger human review when confidence is low even if escalation rule does not strictly fire

## Stage-1 Final Gaps for Stage 2 (OpenAI Agents SDK)
1. Semantic understanding gap:
   - Current rule engine misses indirect language, slang, and implied intent.
   - Stage 2 needs LLM-level intent extraction and contextual reasoning.
2. Threat/churn inference gap:
   - Keyword logic under-prioritizes polite churn threats and commercial risk.
   - Stage 2 needs policy-aware risk scoring beyond exact phrase matching.
3. Robust sentiment modeling gap:
   - Conflicting sentiment ("love product but legal notice") is hard to parse with simple rules.
   - Stage 2 needs nuanced sentiment and frustration trend tracking.
4. Confidence calibration gap:
   - Current confidence is heuristic and static.
   - Stage 2 should use model/logprob signals and calibrated thresholds for fallback/escalation.
5. Response quality gap:
   - Mock responses are template-driven and shallow.
   - Stage 2 must ground responses in real KB retrieval and channel-aware tone adaptation with memory.

## Stage-1 Exit Gate Readiness Snapshot
- Working prototype for multi-channel ticket loop: Completed (`core_loop_v1.py`, `core_loop_v2.py`)
- Discovery log with iterative findings and hard-case analysis: Completed
- Ticket evaluation rubric covering dataset: Completed (`specs/ticket-evaluation-rubric.json`)
- Escalation logic and limitations documented: Completed
- Remaining before Stage-2 build:
  - Implement true tool-based agent runtime (OpenAI Agents SDK)
  - Replace heuristic confidence with model-driven confidence
  - Add persistent memory/state and end-to-end channel integrations

## Exercise 1.3 Completion (Memory and State)
- Prototype: `stage-1-incubation/prototypes/memory_state_v1.py`
- Output report: `specs/memory-state-v1-report.json`
- Run summary:
  - total events processed: 67
  - total customers tracked: 66
  - customers with channel switch: 1 (synthetic continuity validation)
  - escalated customers: 42
- Implemented tracking:
  - conversation memory by customer
  - sentiment score trend (mock heuristic)
  - topics discussed
  - resolution status
  - channel switches

## Exercise 1.4 Completion (MCP Server with 5+ Tools)
- MCP-style tool server: `stage-1-incubation/mcp/customer_success_mcp_server.py`
- Tools implemented:
  1. `search_knowledge_base`
  2. `create_ticket`
  3. `get_customer_history`
  4. `escalate_to_human`
  5. `send_response`
- Smoke test: `stage-1-incubation/mcp/mcp_tools_smoke_test.py`
- Smoke report: `specs/mcp-smoke-test-report.json`
- Smoke test result: pass (all 5 tools returned successful status)

## Exercise 1.5 Completion (Agent Skills + Templates)
- Skills manifest: `.claude/skills/customer-success-fte-stage1/manifest.yaml`
- Stage 1 skill definition: `.claude/skills/customer-success-fte-stage1/SKILL.md`
  - Knowledge Retrieval
  - Sentiment Analysis
  - Escalation Decision
  - Channel Adaptation
  - Customer Identification
- Channel-specific templates: `specs/channel-response-templates.md`
  - Email formal template
  - WhatsApp concise template
  - Web form semi-formal template

## Final Stage 1 Closure
- Exit gate report created: `specs/stage1-exit-gate-report.md`
- Current assessment: Stage 1 incubation deliverables are complete and ready for Stage 2 specialization.
