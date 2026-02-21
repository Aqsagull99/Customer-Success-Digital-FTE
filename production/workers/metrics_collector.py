"""Background metrics collector for the Customer Success FTE."""

from __future__ import annotations

import asyncio
import logging

from database.queries import get_channel_metrics, record_metric
from kafka_client import TOPICS, FTEKafkaConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and aggregate metrics from Kafka events."""

    async def start(self):
        consumer = FTEKafkaConsumer(
            topics=[TOPICS["metrics"]],
            group_id="fte-metrics-collector",
        )
        await consumer.start()
        logger.info("Metrics collector started...")
        await consumer.consume(self.process_metric)

    async def process_metric(self, topic: str, event: dict):
        try:
            await record_metric(
                metric_name=event.get("event_type", "unknown"),
                metric_value=event.get("latency_ms", 0),
                channel=event.get("channel"),
                dimensions=event,
            )
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")


async def main():
    collector = MetricsCollector()
    await collector.start()


if __name__ == "__main__":
    asyncio.run(main())
