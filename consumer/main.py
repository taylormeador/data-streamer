from fastapi import FastAPI
from confluent_kafka import Consumer
import logging
import os
import json
import uuid


logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Consumer", version="0.1.0")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
TOPIC = "iot-sensor-data"


@app.get("/analytics")
async def analytics(limit: int = 10):
    """Read up to `limit` messages from Kafka and return as JSON."""

    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": f"analytics-service-{uuid.uuid4()}",
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe([TOPIC])

    messages = []
    for _ in range(limit):
        msg = consumer.poll(1.0)
        if msg is None:
            break
        if msg.error():
            continue
        try:
            messages.append(json.loads(msg.value().decode("utf-8")))
        except Exception:
            messages.append({"raw": msg.value().decode("utf-8")})

    consumer.close()
    return {"messages": messages}


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}
