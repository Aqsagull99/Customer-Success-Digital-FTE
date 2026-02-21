# Escalation Rules (Template)

## Escalate Immediately
- Security incidents or suspected data breach
- Account lockout with business-critical impact
- Payment disputes, refunds, chargebacks
- Legal/compliance requests
- Repeated user frustration or hostile sentiment

## Escalate If Any Condition Is Met
- Sentiment score < 0.30 for 2+ consecutive messages
- Customer asks for manager/human explicitly
- Agent confidence < threshold (define threshold: )
- Query outside documented product scope
- Same issue unresolved after 2 attempts

## Do Not Escalate (Handle Automatically)
- Basic how-to and onboarding questions
- Known issue with documented workaround
- Status checks that can be answered from system context

## Priority Mapping
- P1: Outage, security, critical workflow blocked
- P2: Core feature unusable for customer
- P3: General support, guidance, minor issues

## Required Escalation Payload
- customer_id
- channel
- conversation summary (3-5 lines)
- attempted actions
- reason for escalation
- urgency/priority
