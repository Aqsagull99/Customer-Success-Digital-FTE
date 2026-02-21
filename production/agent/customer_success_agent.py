"""Customer Success FTE Agent definition using OpenAI Agents SDK."""

from agents import Agent

from agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from agent.tools import (
    create_ticket,
    escalate_to_human,
    get_customer_history,
    search_knowledge_base,
    send_response,
)

customer_success_agent = Agent(
    name="Customer Success FTE",
    model="gpt-4o-mini",
    instructions=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
    tools=[
        search_knowledge_base,
        create_ticket,
        get_customer_history,
        escalate_to_human,
        send_response,
    ],
)
