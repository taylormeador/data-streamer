from prometheus_client import Counter, Gauge, Histogram

# Throughput
messages_processed = Counter("messages_processed", "Total number of messages processed")

# Utilization
workers_busy = Gauge("workers_busy", "Current queue size")
workers_total = Gauge("workers_total", "Total number of workers")

queue_depth = Gauge("queue_depth", "Current queue size")
queue_max_size = Gauge("queue_max_size", "Queue capacity")

db_pool_connections = Gauge("db_pool_connections", "Number of connections in use")
db_pool_connections_max = Gauge(
    "db_pool_connections_max", "Total number of db_pool connections"
)

# Latency
processing_duration_seconds = Histogram(
    "processing_duration_seconds", "Time to process one message"
)
db_write_duration_seconds = Histogram("db_write_duration_seconds", "Time for DB insert")


# Errors
processing_errors = Counter("processing_errors", "Failed message processing")
