from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal
import time
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Data Streamer", version="0.1.0")


# Define schema for telemetry data
class TelemetryEvent(BaseModel):
    device_id: str = Field(..., example="sensor-001")  # type: ignore[no-matching-overload]
    metric: Literal["temperature", "voltage", "humidity", "status"] = Field(
        ..., example="temperature"
    )  # type: ignore[no-matching-overload]
    value: float = Field(..., example=72.5)  # type: ignore[no-matching-overload]
    timestamp: float = Field(default_factory=lambda: time.time())


@app.post("/metrics")
async def ingest_metric(event: TelemetryEvent):
    """
    Ingest a telemetry event. Right now it just logs the event; later this will publish to Kafka.
    """
    logging.info(f"Received event: {event.model_dump()}")
    return {"status": "ok", "event": event.model_dump()}


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}
