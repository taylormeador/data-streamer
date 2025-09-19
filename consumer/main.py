from fastapi import FastAPI
from confluent_kafka import Consumer
import logging
import os
import json
import threading

logging.basicConfig(level=logging.INFO)


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
TOPIC = "iot-sensor-data"

# This will store last N messages for quick retrieval
MESSAGE_CACHE = []

consumer = Consumer(
    {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": "analytics-service",
        "auto.offset.reset": "earliest",
    }
)
consumer.subscribe([TOPIC])
consumer.poll(0)  # Force partition assignment.


def consume_loop():
    while True:
        event = consumer.poll(1.0)
        if event is None:
            continue
        if event.error():
            payload = {"error": event.error()}
        try:
            payload = json.loads(event.value().decode("utf-8"))
        except Exception:
            payload = {"raw": event.value().decode("utf-8")}
        MESSAGE_CACHE.append(payload)

        # Keep last 100 messages
        if len(MESSAGE_CACHE) > 100:
            MESSAGE_CACHE.pop(0)


# Start consumer thread
thread = threading.Thread(target=consume_loop, daemon=True)
thread.start()

app = FastAPI(title="Consumer", version="0.1.0")


@app.get("/analytics")
async def analytics(limit: int = 10):
    """Returns the most recent messages from the cache."""
    return {"messages": MESSAGE_CACHE[-limit:]}


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}
