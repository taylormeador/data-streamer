from prometheus_client import Counter

messages_processed = Counter("messages_processed", "Total number of messages processed")
