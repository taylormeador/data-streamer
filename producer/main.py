from fastapi import FastAPI, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from confluent_kafka import Producer
from pydantic import BaseModel, Field
from typing import Literal, Optional
import time
import logging
import os
import socket
import uuid

import metrics


logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Producer", version="0.1.0")

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
    location: Optional[str] = Field(None, example="warehouse-a")  # type: ignore[no-matching-overload]

    # Fields added during processing (will be None from client)
    message_id: Optional[str] = Field(None)
    ingestion_timestamp: Optional[float] = Field(None)


def delivery_report(err, msg):
    if err is not None:
        logging.error(f"Delivery failed: {err}")
        metrics.kafka_publish_errors.inc()
    else:
        logging.info(
            f"Delivered to {msg.topic()} [{msg.partition()}] offset {msg.offset()}"
        )


@app.post("/ingest")
async def ingest_metric(event: TelemetryEvent):
    """
    Ingests a telemetry event and publishes to Kafka.
    """
    # Add minimal enrichment to create some CPU work
    enrich_start = time.time()
    enriched_event = event.model_copy()
    enriched_event.message_id = str(uuid.uuid4())
    enriched_event.ingestion_timestamp = time.time()
    metrics.enrichment_duration.observe(time.time() - enrich_start)

    logging.info(f"Received event: {enriched_event.model_dump()}")

    publish_start = time.time()
    producer.produce(
        TOPIC,
        key=event.device_id,
        value=enriched_event.model_dump_json(),
        callback=delivery_report,
    )
    producer.flush()
    metrics.kafka_publish_duration.observe(time.time() - publish_start)
    metrics.kafka_messages_published.inc()

    return {"status": "ok", "message_id": enriched_event.message_id}


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}
