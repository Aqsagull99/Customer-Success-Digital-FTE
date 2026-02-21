"""Kafka event streaming client for the Customer Success FTE."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Callable, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

# Topic definitions for multi-channel FTE
TOPICS = {
    # Incoming tickets from all channels
    "tickets_incoming": "fte.tickets.incoming",
    # Channel-specific inbound
    "email_inbound": "fte.channels.email.inbound",
    "whatsapp_inbound": "fte.channels.whatsapp.inbound",
    "webform_inbound": "fte.channels.webform.inbound",
    # Channel-specific outbound
    "email_outbound": "fte.channels.email.outbound",
    "whatsapp_outbound": "fte.channels.whatsapp.outbound",
    # Escalations
    "escalations": "fte.escalations",
    # Metrics and monitoring
    "metrics": "fte.metrics",
    # Dead letter queue for failed processing
    "dlq": "fte.dlq",
}

_producer: Optional[FTEKafkaProducer] = None


class FTEKafkaProducer:
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def publish(self, topic: str, event: dict):
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        await self.producer.send_and_wait(topic, event)


class FTEKafkaConsumer:
    def __init__(self, topics: list[str], group_id: str):
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

    async def start(self):
        await self.consumer.start()

    async def stop(self):
        await self.consumer.stop()

    async def consume(self, handler: Callable):
        async for msg in self.consumer:
            await handler(msg.topic, msg.value)


async def get_kafka_producer() -> FTEKafkaProducer:
    """Get or create the singleton Kafka producer."""
    global _producer
    if _producer is None:
        _producer = FTEKafkaProducer()
        await _producer.start()
    return _producer
