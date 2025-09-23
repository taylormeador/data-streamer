from fastapi import FastAPI
from confluent_kafka import Consumer
import logging
import os
import json
import threading
from collections import defaultdict
import statistics
import time
from typing import Dict, List, Optional, TypedDict

logging.basicConfig(level=logging.INFO)


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
TOPIC = "iot-sensor-data"

# This will store last N messages for quick retrieval
MESSAGE_CACHE = []


# Aggregate computation
class DeviceStats(TypedDict):
    count: int
    values: List[float]
    last_seen: Optional[float]
    avg_value: float


DEVICE_STATS: Dict[str, DeviceStats] = defaultdict(
    lambda: {"count": 0, "values": [], "last_seen": None, "avg_value": 0.0}
)


# Init Kafka consumer
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
    "Polls the topic in Kafka in the background and processes messages as they arrive."
    while True:
        event = consumer.poll(1.0)
        if event is None:
            continue
        if event.error():
            logging.error(f"Consumer error: {event.error()}")
            continue

        try:
            payload = json.loads(event.value().decode("utf-8"))
            processed_payload = process_message(payload)
            MESSAGE_CACHE.append(processed_payload)
            if len(MESSAGE_CACHE) > 100:
                MESSAGE_CACHE.pop(0)

        except Exception as e:
            logging.error(f"Error processing message: {e}")


def process_message(payload):
    """Add computational work to create benchmarkable bottlenecks."""
    device_id = payload.get("device_id")
    metric = payload.get("metric")
    value = payload.get("value")
    anomaly_detected = False

    if device_id and metric and value is not None:
        # Update device statistics
        stats = DEVICE_STATS[device_id]
        stats["count"] += 1
        stats["values"].append(value)
        stats["last_seen"] = time.time()

        # Keep only last 100 values per device
        if len(stats["values"]) > 100:
            stats["values"] = stats["values"][-100:]

        # Calculate running statistics
        stats["avg_value"] = statistics.mean(stats["values"])

        # Anomaly detection
        if len(stats["values"]) >= 10:
            recent_avg = statistics.mean(stats["values"][-10:])
            overall_avg = stats["avg_value"]
            deviation = (
                abs(recent_avg - overall_avg) / overall_avg if overall_avg != 0 else 0
            )
            anomaly_detected = deviation > 0.2  # 20% deviation threshold

    # Enrich the payload with processing results
    enriched_payload = {
        **payload,
        "processed_at": time.time(),
        "anomaly_detected": anomaly_detected,
    }

    return enriched_payload


# Start consumer thread
thread = threading.Thread(target=consume_loop, daemon=True)
thread.start()

app = FastAPI(title="Consumer", version="0.1.0")


# Routes
@app.get("/analytics")
async def analytics(limit: int = 10):
    """Returns the most recent messages from the cache."""
    return {"messages": MESSAGE_CACHE[-limit:]}


@app.get("/device-stats")
async def device_statistics():
    """Returns aggregated statistics per device."""
    stats_summary = {}
    for device_id, stats in DEVICE_STATS.items():
        stats_summary[device_id] = {
            "message_count": stats["count"],
            "avg_value": round(stats["avg_value"], 2),
            "last_seen": stats["last_seen"],
            "recent_values": stats["values"][-5:] if stats["values"] else [],
        }
    return {"device_stats": stats_summary}


@app.get("/anomalies")
async def recent_anomalies(limit: int = 20):
    """Returns recent messages flagged as anomalies."""
    anomalies = [msg for msg in MESSAGE_CACHE if msg.get("anomaly_detected")]
    return {"anomalies": anomalies[-limit:]}


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}
