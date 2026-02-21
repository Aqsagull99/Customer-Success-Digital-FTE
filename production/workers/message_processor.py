"""Unified message processor: consumes Kafka events, runs the FTE agent."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from agent.customer_success_agent import customer_success_agent
from agent.formatters import Channel
from channels.gmail_handler import GmailHandler
from channels.whatsapp_handler import WhatsAppHandler
from database.queries import (
    create_conversation,
    create_customer,
    find_customer_by_email,
    find_customer_by_phone,
    get_active_conversation,
    load_conversation_messages,
    store_message,
)
from kafka_client import TOPICS, FTEKafkaConsumer, get_kafka_producer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UnifiedMessageProcessor:
    """Process incoming messages from all channels through the FTE agent."""

    def __init__(self):
        self.gmail = GmailHandler()
        self.whatsapp = WhatsAppHandler()

    async def start(self):
        """Start the message processor."""
        producer = await get_kafka_producer()

        consumer = FTEKafkaConsumer(
            topics=[TOPICS["tickets_incoming"]],
            group_id="fte-message-processor",
        )
        await consumer.start()

        logger.info("Message processor started, listening for tickets...")
        await consumer.consume(self.process_message)

    async def process_message(self, topic: str, message: dict):
        """Process a single incoming message from any channel."""
        try:
            start_time = datetime.now(timezone.utc)

            channel = Channel(message["channel"])
            customer_id = await self.resolve_customer(message)
            conversation_id = await self.get_or_create_conversation(
                customer_id=customer_id,
                channel=channel,
                message=message,
            )

            # Store incoming message
            await store_message(
                conversation_id=conversation_id,
                channel=channel.value,
                direction="inbound",
                role="customer",
                content=message["content"],
                channel_message_id=message.get("channel_message_id"),
            )

            # Load conversation history
            history_rows = await load_conversation_messages(conversation_id)
            history = [
                {"role": r["role"], "content": r["content"]} for r in reversed(history_rows)
            ]

            # Run agent
            from agents import Runner

            result = await Runner.run(
                customer_success_agent,
                input=history,
                context={
                    "customer_id": customer_id,
                    "conversation_id": conversation_id,
                    "channel": channel.value,
                    "ticket_subject": message.get("subject", "Support Request"),
                    "metadata": message.get("metadata", {}),
                },
            )

            latency_ms = int(
                (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            )

            # Store agent response
            await store_message(
                conversation_id=conversation_id,
                channel=channel.value,
                direction="outbound",
                role="agent",
                content=result.final_output,
                latency_ms=latency_ms,
            )

            # Publish metrics
            producer = await get_kafka_producer()
            await producer.publish(
                TOPICS["metrics"],
                {
                    "event_type": "message_processed",
                    "channel": channel.value,
                    "latency_ms": latency_ms,
                },
            )

            logger.info(f"Processed {channel.value} message in {latency_ms}ms")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.handle_error(message, e)

    async def resolve_customer(self, message: dict) -> str:
        """Resolve or create customer from message identifiers."""
        email = message.get("customer_email")
        if email:
            customer = await find_customer_by_email(email)
            if customer:
                return str(customer["id"])
            return await create_customer(
                email=email, name=message.get("customer_name", "")
            )

        phone = message.get("customer_phone")
        if phone:
            customer = await find_customer_by_phone(phone)
            if customer:
                return str(customer["id"])
            return await create_customer(phone=phone)

        raise ValueError("Could not resolve customer from message")

    async def get_or_create_conversation(
        self, customer_id: str, channel: Channel, message: dict
    ) -> str:
        """Get active conversation or create new one."""
        active = await get_active_conversation(customer_id)
        if active:
            return str(active["id"])
        return await create_conversation(customer_id, channel.value)

    async def handle_error(self, message: dict, error: Exception):
        """Handle processing errors gracefully."""
        channel = Channel(message["channel"])
        apology = "I'm sorry, I'm having trouble processing your request right now. A human agent will follow up shortly."

        try:
            if channel == Channel.EMAIL and message.get("customer_email"):
                await self.gmail.send_reply(
                    to_email=message["customer_email"],
                    subject=message.get("subject", "Support Request"),
                    body=apology,
                )
            elif channel == Channel.WHATSAPP and message.get("customer_phone"):
                await self.whatsapp.send_message(
                    to_phone=message["customer_phone"],
                    body=apology,
                )
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")

        # Publish for human review
        producer = await get_kafka_producer()
        await producer.publish(
            TOPICS["escalations"],
            {
                "event_type": "processing_error",
                "original_message": message,
                "error": str(error),
                "requires_human": True,
            },
        )


async def main():
    processor = UnifiedMessageProcessor()
    await processor.start()


if __name__ == "__main__":
    asyncio.run(main())
