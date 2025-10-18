from prometheus_client import Counter, Histogram

prefix = "PRODUCER"  # Included for ease of searching in Grafana

# Track messages published
kafka_messages_published = Counter(
    f"{prefix}_kafka_messages_published_total",
    "Total messages published to Kafka",
)

# Track Kafka publish duration
kafka_publish_duration = Histogram(
    f"{prefix}_kafka_publish_duration_seconds",
    "Time to publish message to Kafka",
)

# Track errors
kafka_publish_errors = Counter(
    f"{prefix}_kafka_publish_errors_total", "Failed Kafka publishes"
)
