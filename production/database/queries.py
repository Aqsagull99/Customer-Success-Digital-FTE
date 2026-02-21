"""Database access functions for the Customer Success FTE."""

from __future__ import annotations

import os
from typing import Optional

import asyncpg

_pool: Optional[asyncpg.Pool] = None

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fte_user:fte_pass@localhost:5432/fte_db",
)


async def get_db_pool() -> asyncpg.Pool:
    """Get or create the database connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    return _pool


async def close_db_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


# -- Customer queries --

async def find_customer_by_email(email: str) -> Optional[asyncpg.Record]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM customers WHERE email = $1", email)


async def find_customer_by_phone(phone: str) -> Optional[asyncpg.Record]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT c.* FROM customers c
               JOIN customer_identifiers ci ON ci.customer_id = c.id
               WHERE ci.identifier_type = 'whatsapp' AND ci.identifier_value = $1""",
            phone,
        )
        return row


async def create_customer(email: Optional[str] = None, phone: Optional[str] = None, name: str = "") -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        customer_id = await conn.fetchval(
            "INSERT INTO customers (email, phone, name) VALUES ($1, $2, $3) RETURNING id",
            email, phone, name,
        )
        if phone:
            await conn.execute(
                """INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value)
                   VALUES ($1, 'whatsapp', $2)
                   ON CONFLICT DO NOTHING""",
                customer_id, phone,
            )
        return str(customer_id)


# -- Conversation queries --

async def get_active_conversation(customer_id: str) -> Optional[asyncpg.Record]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """SELECT * FROM conversations
               WHERE customer_id = $1 AND status = 'active'
                 AND started_at > NOW() - INTERVAL '24 hours'
               ORDER BY started_at DESC LIMIT 1""",
            customer_id,
        )


async def create_conversation(customer_id: str, channel: str) -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        return str(await conn.fetchval(
            """INSERT INTO conversations (customer_id, initial_channel, status)
               VALUES ($1, $2, 'active') RETURNING id""",
            customer_id, channel,
        ))


async def load_conversation_messages(conversation_id: str, limit: int = 20) -> list:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT role, content, channel, created_at
               FROM messages WHERE conversation_id = $1
               ORDER BY created_at DESC LIMIT $2""",
            conversation_id, limit,
        )
        return [dict(r) for r in rows]


# -- Message queries --

async def store_message(
    conversation_id: str,
    channel: str,
    direction: str,
    role: str,
    content: str,
    channel_message_id: Optional[str] = None,
    latency_ms: Optional[int] = None,
    tool_calls: Optional[list] = None,
) -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        import json
        return str(await conn.fetchval(
            """INSERT INTO messages
               (conversation_id, channel, direction, role, content,
                channel_message_id, latency_ms, tool_calls)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
               RETURNING id""",
            conversation_id, channel, direction, role, content,
            channel_message_id, latency_ms,
            json.dumps(tool_calls or []),
        ))


# -- Ticket queries --

async def create_ticket_record(
    customer_id: str,
    conversation_id: str,
    channel: str,
    category: Optional[str] = None,
    priority: str = "medium",
) -> str:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        return str(await conn.fetchval(
            """INSERT INTO tickets
               (customer_id, conversation_id, source_channel, category, priority, status)
               VALUES ($1, $2, $3, $4, $5, 'open')
               RETURNING id""",
            customer_id, conversation_id, channel, category, priority,
        ))


async def update_ticket_status(ticket_id: str, status: str, resolution_notes: Optional[str] = None) -> None:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        if status in ("resolved", "closed"):
            await conn.execute(
                """UPDATE tickets SET status = $1, resolution_notes = $2, resolved_at = NOW()
                   WHERE id = $3""",
                status, resolution_notes, ticket_id,
            )
        else:
            await conn.execute(
                "UPDATE tickets SET status = $1, resolution_notes = $2 WHERE id = $3",
                status, resolution_notes, ticket_id,
            )


async def get_ticket_by_id(ticket_id: str) -> Optional[dict]:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tickets WHERE id = $1", ticket_id)
        return dict(row) if row else None


# -- Customer history (cross-channel) --

async def get_customer_history_records(customer_id: str, limit: int = 20) -> list:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT c.initial_channel, c.started_at, c.status,
                      m.content, m.role, m.channel, m.created_at
               FROM conversations c
               JOIN messages m ON m.conversation_id = c.id
               WHERE c.customer_id = $1
               ORDER BY m.created_at DESC LIMIT $2""",
            customer_id, limit,
        )
        return [dict(r) for r in rows]


# -- Knowledge base --

async def search_knowledge_base_records(embedding: list, max_results: int = 5, category: Optional[str] = None) -> list:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        if category:
            rows = await conn.fetch(
                """SELECT title, content, category,
                          1 - (embedding <=> $1::vector) as similarity
                   FROM knowledge_base
                   WHERE category = $2
                   ORDER BY embedding <=> $1::vector LIMIT $3""",
                str(embedding), category, max_results,
            )
        else:
            rows = await conn.fetch(
                """SELECT title, content, category,
                          1 - (embedding <=> $1::vector) as similarity
                   FROM knowledge_base
                   ORDER BY embedding <=> $1::vector LIMIT $2""",
                str(embedding), max_results,
            )
        return [dict(r) for r in rows]


# -- Metrics --

async def record_metric(metric_name: str, metric_value: float, channel: Optional[str] = None, dimensions: Optional[dict] = None) -> None:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        import json
        await conn.execute(
            """INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions)
               VALUES ($1, $2, $3, $4::jsonb)""",
            metric_name, metric_value, channel, json.dumps(dimensions or {}),
        )


async def get_channel_metrics() -> list:
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT initial_channel as channel,
                      COUNT(*) as total_conversations,
                      AVG(sentiment_score) as avg_sentiment,
                      COUNT(*) FILTER (WHERE status = 'escalated') as escalations
               FROM conversations
               WHERE started_at > NOW() - INTERVAL '24 hours'
               GROUP BY initial_channel""",
        )
        return [dict(r) for r in rows]
