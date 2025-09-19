from fastapi import FastAPI
from confluent_kafka import Producer, Consumer
from pydantic import BaseModel, Field
from typing import Literal
import time
import logging
import os
import socket
import json
import uuid


logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Data Streamer", version="0.1.0")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
TOPIC = "iot-sensor-data"

conf = {
    "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    "client.id": socket.gethostname(),
}
producer = Producer(conf)


# Define schema for telemetry data
class TelemetryEvent(BaseModel):
    device_id: str = Field(..., example="sensor-001")  # type: ignore[no-matching-overload]
    metric: Literal["temperature", "voltage", "humidity", "status"] = Field(
        ..., example="temperature"
    )  # type: ignore[no-matching-overload]
    value: float = Field(..., example=72.5)  # type: ignore[no-matching-overload]
    timestamp: float = Field(default_factory=lambda: time.time())


def delivery_report(err, msg):
    if err is not None:
        logging.error(f"Delivery failed: {err}")
    else:
        logging.info(
            f"Delivered to {msg.topic()} [{msg.partition()}] offset {msg.offset()}"
        )


@app.post("/ingest")
async def ingest_metric(event: TelemetryEvent):
    """
    Ingest a telemetry event. Right now it just logs the event; later this will publish to Kafka.
    """
    logging.info(f"Received event: {event.model_dump()}")

    producer.produce(
        TOPIC,
        key=event.device_id,
        value=event.model_dump_json(),
        callback=delivery_report,
    )
    producer.flush()

    return {"status": "ok", "event": event.model_dump()}


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
