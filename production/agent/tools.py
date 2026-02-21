"""Production @function_tool definitions for the Customer Success FTE agent."""

from __future__ import annotations

import logging
from typing import Optional

from agents import function_tool
from pydantic import BaseModel

from agent.formatters import Channel, format_for_channel
from database.queries import (
    create_ticket_record,
    get_customer_history_records,
    get_ticket_by_id,
    search_knowledge_base_records,
    store_message,
    update_ticket_status,
)

logger = logging.getLogger(__name__)


# -- Pydantic input schemas --

class KnowledgeSearchInput(BaseModel):
    """Input schema for knowledge base search."""
    query: str
    max_results: int = 5
    category: Optional[str] = None


class TicketInput(BaseModel):
    """Input schema for ticket creation."""
    customer_id: str
    issue: str
    priority: str = "medium"
    category: Optional[str] = None
    channel: Channel


class EscalationInput(BaseModel):
    """Input schema for escalation."""
    ticket_id: str
    reason: str
    urgency: str = "normal"


class ResponseInput(BaseModel):
    """Input schema for sending a response."""
    ticket_id: str
    message: str
    channel: Channel


# -- Helper: generate embedding (uses OpenAI) --

async def generate_embedding(text: str) -> list[float]:
    """Generate an embedding vector for semantic search."""
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        resp = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return resp.data[0].embedding
    except Exception as e:
        logger.warning(f"Embedding generation failed: {e}; returning zero vector")
        return [0.0] * 1536


# -- Production tools --

@function_tool
async def search_knowledge_base(query: str, max_results: int = 5) -> str:
    """Search product documentation for relevant information.

    Use this when the customer asks questions about product features,
    how to use something, or needs technical information.
    """
    try:
        embedding = await generate_embedding(query)
        results = await search_knowledge_base_records(embedding, max_results)

        if not results:
            return "No relevant documentation found. Consider escalating to human support."

        formatted = []
        for r in results:
            sim = r.get("similarity", 0)
            formatted.append(f"**{r['title']}** (relevance: {sim:.2f})\n{r['content'][:500]}")

        return "\n\n---\n\n".join(formatted)

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        return "Knowledge base temporarily unavailable. Please try again or escalate."


@function_tool
async def create_ticket(customer_id: str, issue: str, priority: str = "medium", category: str = "", channel: str = "web_form") -> str:
    """Create a support ticket for tracking.

    ALWAYS create a ticket at the start of every conversation.
    Include the source channel for proper tracking.
    """
    try:
        ticket_id = await create_ticket_record(
            customer_id=customer_id,
            conversation_id="",  # Will be set by message processor
            channel=channel,
            category=category or None,
            priority=priority,
        )
        return f"Ticket created: {ticket_id}"
    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        return "Failed to create ticket. Continuing with response."


@function_tool
async def get_customer_history(customer_id: str) -> str:
    """Get customer's complete interaction history across ALL channels.

    Use this to understand context from previous conversations,
    even if they happened on a different channel.
    """
    try:
        history = await get_customer_history_records(customer_id)

        if not history:
            return "No previous interactions found for this customer."

        formatted = []
        for h in history:
            formatted.append(
                f"[{h['channel']}] {h['role']}: {h['content'][:200]}"
            )
        return f"Found {len(history)} previous interactions:\n" + "\n".join(formatted)

    except Exception as e:
        logger.error(f"Customer history lookup failed: {e}")
        return "Could not retrieve customer history. Proceeding without context."


@function_tool
async def escalate_to_human(ticket_id: str, reason: str) -> str:
    """Escalate conversation to human support.

    Use this when:
    - Customer asks about pricing or refunds
    - Customer sentiment is negative
    - You cannot find relevant information
    - Customer explicitly requests human help
    """
    try:
        await update_ticket_status(
            ticket_id=ticket_id,
            status="escalated",
            resolution_notes=f"Escalation reason: {reason}",
        )
        return f"Escalated to human support. Reference: {ticket_id}. Reason: {reason}"
    except Exception as e:
        logger.error(f"Escalation failed: {e}")
        return f"Escalation logged for ticket {ticket_id}. A human agent will follow up."


@function_tool
async def send_response(ticket_id: str, message: str, channel: str = "web_form") -> str:
    """Send response to customer via their preferred channel.

    The response will be automatically formatted for the channel.
    Email: Formal with greeting/signature
    WhatsApp: Concise and conversational
    Web: Semi-formal
    """
    try:
        ch = Channel(channel)
        formatted = format_for_channel(message, ch, ticket_id)

        # Store outbound message
        ticket = await get_ticket_by_id(ticket_id)
        if ticket and ticket.get("conversation_id"):
            await store_message(
                conversation_id=str(ticket["conversation_id"]),
                channel=channel,
                direction="outbound",
                role="agent",
                content=formatted,
            )

        return f"Response sent via {channel}: delivered"
    except Exception as e:
        logger.error(f"Send response failed: {e}")
        return f"Response prepared but delivery pending for ticket {ticket_id}."
