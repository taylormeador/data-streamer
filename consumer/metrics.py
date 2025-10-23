from prometheus_client import Counter, Histogram, Gauge

prefix = "CONSUMER"

# Input Metrics

# Track messages consumed from Kafka
kafka_messages_consumed = Counter(
    f"{prefix}_kafka_messages_consumed_total",
    "Total messages consumed from Kafka",
    ["topic"],
)

# Track batch sizes
batch_size = Histogram(
    f"{prefix}_batch_size",
    "Number of messages in each batch",
    buckets=[1, 5, 10, 25, 50, 100, 250, 500],
)

# Validation Metrics

# Track validation results
messages_validated = Counter(
    f"{prefix}_messages_validated_total",
    "Messages that passed validation",
)

messages_rejected = Counter(
    f"{prefix}_messages_rejected_total",
    "Messages that failed validation",
    ["reason"],  # Label to track WHY messages were rejected
)

# Track validation duration
validation_duration = Histogram(
    f"{prefix}_validation_duration_seconds",
    "Time to validate a batch of messages",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Enrichment Metrics

enrichment_duration = Histogram(
    f"{prefix}_enrichment_duration_seconds",
    "Time to enrich a batch of messages",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Output Metrics

# Track messages published (to validated topic)
kafka_messages_published = Counter(
    f"{prefix}_kafka_messages_published_total",
    "Total messages published to Kafka",
    ["topic"],
)

# Track Kafka publish duration
kafka_publish_duration = Histogram(
    f"{prefix}_kafka_publish_duration_seconds",
    "Time to publish message to Kafka",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Track errors
kafka_publish_errors = Counter(
    f"{prefix}_kafka_publish_errors_total", "Failed Kafka publishes", ["topic"]
)

# Health Metrics

# Track current lag (if available)
consumer_lag = Gauge(
    f"{prefix}_consumer_lag", "Current consumer lag", ["topic", "partition"]
)

# Track processing pipeline health
messages_in_flight = Gauge(
    f"{prefix}_messages_in_flight", "Messages currently being processed"
)
