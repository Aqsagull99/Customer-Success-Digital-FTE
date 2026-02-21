# Stage 1 Day-1 Prompt Pack (Copy/Paste)

## Prompt 1: Initial Exploration (Exercise 1.1)
I need to build a Customer Success AI agent for a SaaS company.

The agent should:
- Answer customer questions from product documentation
- Accept tickets from THREE channels: Gmail, WhatsApp, and a Web Form
- Know when to escalate to humans
- Track all interactions with channel source metadata

I've provided company context in the /context folder.
Help me explore what this system should look like.
Start by analyzing the sample tickets and identifying patterns across channels.

Output format:
1. Top 10 discovered patterns from sample tickets
2. Channel differences (email vs whatsapp vs web form)
3. Missing requirements and assumptions
4. Proposed minimal architecture for a prototype
5. Open questions I should answer before coding

## Prompt 2: Build Core Loop (Exercise 1.2)
Based on our analysis, let's prototype the core customer interaction loop.
Build a simple version that:
1. Takes a customer message as input (with channel metadata)
2. Normalizes the message regardless of source channel
3. Searches the product docs for relevant information
4. Generates a helpful response
5. Formats response appropriately for the channel (email vs chat style)
6. Decides if escalation is needed

Use Python. Start simple and iterate.

Constraints:
- Keep functions small and testable
- Add structured logging
- Return a JSON object with:
  - customer_id
  - channel
  - normalized_message
  - response_text
  - should_escalate
  - escalation_reason

## Prompt 3: Iteration - Pricing Edge Case
This crashes when the customer asks about pricing.
Add handling for pricing-related queries, including:
- Detection logic
- Escalation rule alignment
- Safe customer-facing response

## Prompt 4: Iteration - WhatsApp Style
WhatsApp messages are shorter and more casual.
Adjust response style based on channel.
- WhatsApp: concise and conversational
- Email: detailed and formal
- Web form: semi-formal

## Prompt 5: Iteration - Email Format
Email responses need proper greeting and signature.
Add channel-aware email formatting with:
- Greeting
- Body
- Signature
- Subject suggestion

## Prompt 6: Iteration - Response Length
Responses are too long for WhatsApp.
Optimize for brevity on chat channels while keeping detail on email.
Set and enforce channel max length limits.

## Prompt 7: Add Memory and State (Exercise 1.3)
Our agent needs to remember context across a conversation.
If a customer asks follow-up questions, it should understand continuity even if they switch channels.

Add:
- Conversation memory
- Sentiment tracking
- Topics tracking
- Resolution status (solved/pending/escalated)
- Original channel and channel switch tracking
- Customer identifier (email as primary key)

Also provide tests for channel switching behavior.

## Prompt 8: Build MCP Server (Exercise 1.4)
Expose this prototype as an MCP server with tools:
- search_knowledge_base(query)
- create_ticket(customer_id, issue, priority, channel)
- get_customer_history(customer_id)
- escalate_to_human(ticket_id, reason)
- send_response(ticket_id, message, channel)

Requirements:
- Use typed input schemas
- Add basic validation and error handling
- Return structured outputs

## Prompt 9: Define Skills Manifest (Exercise 1.5)
Create a reusable skills manifest for:
1. Knowledge Retrieval Skill
2. Sentiment Analysis Skill
3. Escalation Decision Skill
4. Channel Adaptation Skill
5. Customer Identification Skill

For each skill include:
- when_to_use
- inputs
- outputs
- failure_modes
- example_invocation

## Prompt 10: Stage-1 Readiness Check
Evaluate my Stage 1 status against this checklist:
- Working prototype for all channels
- specs/discovery-log.md updated
- specs/customer-success-fte-spec.md drafted
- MCP server with 5+ tools
- Skills manifest complete
- 20+ edge cases per channel documented
- Baseline metrics measured

Return:
1. Pass/Fail per item
2. Exact gaps
3. Next 3 actions in priority order
