"""Customer Success FTE Agent definition using Groq (free AI)."""

import os
from typing import Any

from agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT

# Check if using Groq (free alternative to OpenAI)
USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

if USE_GROQ and GROQ_API_KEY:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    DEFAULT_MODEL = "llama-3.3-70b-versatile"  # Groq's free model
else:
    from openai import OpenAI
    client = OpenAI()
    DEFAULT_MODEL = "gpt-4o-mini"


class SimpleAgent:
    """Simple agent wrapper that works with Groq or OpenAI."""
    
    def __init__(self, name: str, model: str, system_prompt: str):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.tools = []
        
    def add_tool(self, tool):
        self.tools.append(tool)
        
    async def run(self, input_messages: list, context: dict = None) -> "AgentResult":
        """Run the agent with Groq/OpenAI."""
        # Build messages with system prompt
        messages = [
            {"role": "system", "content": self.system_prompt},
            *input_messages
        ]
        
        # Call the API
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        
        return AgentResult(final_output=response.choices[0].message.content)


class AgentResult:
    def __init__(self, final_output: str):
        self.final_output = final_output


# Create the agent with tools
customer_success_agent = SimpleAgent(
    name="Customer Success FTE",
    model=DEFAULT_MODEL,
    system_prompt=CUSTOMER_SUCCESS_SYSTEM_PROMPT,
)

# Add tools for later use (not used in simple mode)
from agent.tools import search_knowledge_base, create_ticket, get_customer_history, escalate_to_human, send_response
for tool in [search_knowledge_base, create_ticket, get_customer_history, escalate_to_human, send_response]:
    customer_success_agent.add_tool(tool)
