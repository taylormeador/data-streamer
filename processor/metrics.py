from prometheus_client import Counter, Gauge, Histogram

prefix = f"PROCESSOR"

# Throughput
messages_processed = Counter(
    f"{prefix}_messages_processed", "Total number of messages processed"
)

# Utilization
workers_busy = Gauge(f"{prefix}_workers_busy", "Current queue size")
workers_total = Gauge(f"{prefix}_workers_total", "Total number of workers")

queue_depth = Gauge(f"{prefix}_queue_depth", "Current queue size")
queue_max_size = Gauge(f"{prefix}_queue_max_size", "Queue capacity")

db_pool_connections = Gauge(
    f"{prefix}_db_pool_connections", "Number of connections in use"
)
db_pool_connections_max = Gauge(
    f"{prefix}_db_pool_connections_max", "Total number of db_pool connections"
)

# Latency
processing_duration_seconds = Histogram(
    f"{prefix}_processing_duration_seconds", "Time to process one message"
)
db_write_duration_seconds = Histogram(
    f"{prefix}_db_write_duration_seconds", "Time for DB insert"
)


# Errors
processing_errors = Counter(f"{prefix}_processing_errors", "Failed message processing")
