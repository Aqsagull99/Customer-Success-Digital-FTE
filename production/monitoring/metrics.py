"""Prometheus metrics for the Customer Success FTE."""

from prometheus_client import Counter, Gauge, Histogram

# --- Request metrics ---
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# --- Agent metrics ---
fte_messages_processed = Counter(
    "fte_messages_processed_total",
    "Total messages processed by the agent",
    ["channel"],
)

fte_agent_processing = Histogram(
    "fte_agent_processing_seconds",
    "Agent processing time per message",
    ["channel"],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 30.0],
)

fte_escalations = Counter(
    "fte_escalations_total",
    "Total escalations to human agents",
    ["channel", "reason"],
)

# --- Channel health ---
fte_channel_health = Gauge(
    "fte_channel_health",
    "Channel health status (1=healthy, 0=down)",
    ["channel"],
)

# --- Kafka metrics ---
fte_kafka_consumer_lag = Gauge(
    "fte_kafka_consumer_lag",
    "Kafka consumer lag per topic",
    ["topic", "partition"],
)

fte_kafka_messages_published = Counter(
    "fte_kafka_messages_published_total",
    "Total messages published to Kafka",
    ["topic"],
)

# --- Database metrics ---
fte_db_connection_errors = Counter(
    "fte_db_connection_errors_total",
    "Database connection errors",
)

fte_db_query_duration = Histogram(
    "fte_db_query_duration_seconds",
    "Database query duration",
    ["query_type"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5],
)

# --- Sentiment tracking ---
fte_sentiment_score = Histogram(
    "fte_sentiment_score",
    "Customer sentiment score distribution",
    ["channel"],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)
