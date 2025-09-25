from fastapi import FastAPI
from confluent_kafka import Consumer
import logging
import os
import json
import threading
import time
import asyncio
from contextlib import asynccontextmanager
import asyncpg
import uuid

logging.basicConfig(level=logging.INFO)

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://iot_user:iot_password@postgres:5432/iot_platform"
)
TOPIC = "iot-sensor-data"

# Global database pool for API endpoints
api_db_pool = None
# Separate connection for consumer thread
consumer_db_pool = None

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


async def get_device_stats(device_id: str, metric: str, pool, limit: int = 100):
    """Get recent readings for a specific device and metric type"""
    query = """
        SELECT value, timestamp 
        FROM device_readings 
        WHERE device_id = $1 AND metric = $2
        ORDER BY processed_at DESC 
        LIMIT $3
    """
    async with pool.acquire() as connection:
        results = await connection.fetch(query, device_id, metric, limit)
        return [float(row["value"]) for row in results]


async def store_device_reading(
    payload: dict,
    anomaly_detected: bool,
    rolling_avg: float,
    deviation_pct: float,
    pool,
):
    """Store processed reading in PostgreSQL"""
    query = """
        INSERT INTO device_readings (
            device_id, metric, value, timestamp, ingestion_timestamp, 
            message_id, location, anomaly_detected, rolling_avg, deviation_pct, processed_at
        ) VALUES (
            $1, $2, $3, to_timestamp($4), 
            to_timestamp($5), $6::uuid, 
            $7, $8, $9, $10, NOW()
        )
    """

    values = (
        payload.get("device_id"),
        payload.get("metric"),
        payload.get("value"),
        payload.get("timestamp"),
        payload.get("ingestion_timestamp", time.time()),
        payload.get("message_id"),
        payload.get("location"),
        anomaly_detected,
        rolling_avg,
        deviation_pct,
    )

    try:
        async with pool.acquire() as connection:
            await connection.execute(query, *values)
        logging.debug(f"Stored reading for device {payload.get('device_id')}")
    except Exception as e:
        logging.error(f"Failed to store reading: {e}")
        raise


async def process_message(payload, pool):
    """Process message and store in database"""
    device_id = payload.get("device_id")
    metric = payload.get("metric")
    value = payload.get("value")
    anomaly_detected = False
    rolling_avg = 0.0
    deviation_pct = 0.0

    if device_id and metric and value is not None:
        # Get recent readings for this specific device + metric combination
        recent_values = await get_device_stats(device_id, metric, pool, limit=100)
        all_values = [value] + recent_values

        if len(all_values) >= 1:
            rolling_avg = sum(all_values) / len(all_values)

            # Only detect anomalies if we have enough historical data
            if len(all_values) >= 10:
                recent_avg = sum(all_values[:5]) / 5  # Last 5 readings
                historical_avg = sum(all_values[5:]) / len(
                    all_values[5:]
                )  # Historical baseline

                if historical_avg != 0:
                    deviation_pct = abs(recent_avg - historical_avg) / historical_avg
                    # Use metric-specific thresholds
                    thresholds = {
                        "temperature": 0.15,  # 15% for temperature
                        "humidity": 0.20,  # 20% for humidity
                        "voltage": 0.10,  # 10% for voltage (more sensitive)
                        "status": 0.50,  # 50% for status values
                    }
                    threshold = thresholds.get(metric, 0.20)
                    anomaly_detected = deviation_pct > threshold
                else:
                    deviation_pct = 0.0

        await store_device_reading(
            payload, anomaly_detected, rolling_avg, deviation_pct, pool
        )
        logging.debug(
            f"Processed {device_id}/{metric}: avg={rolling_avg:.2f}, anomaly={anomaly_detected}"
        )


def consume_loop():
    """Polls the topic in Kafka in the background and processes messages as they arrive."""

    async def async_consume():
        global consumer_db_pool

        # Create separate database pool for consumer thread with retry logic
        max_retries = 30
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                consumer_db_pool = await asyncpg.create_pool(
                    DATABASE_URL, min_size=1, max_size=5
                )
                logging.info("Consumer thread connected to database")
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(
                        f"Consumer failed to connect to database after {max_retries} attempts: {e}"
                    )
                    return
                logging.warning(
                    f"Consumer database connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)

        while True:
            event = consumer.poll(1.0)
            if event is None:
                continue
            if event.error():
                logging.error(f"Consumer error: {event.error()}")
                continue

            try:
                payload = json.loads(event.value().decode("utf-8"))
                await process_message(payload, consumer_db_pool)
            except Exception as e:
                logging.error(f"Error processing message: {e}")
                import traceback

                traceback.print_exc()

    # Run async consume in new event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_consume())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    global api_db_pool

    # Startup with retry logic
    max_retries = 30
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            api_db_pool = await asyncpg.create_pool(
                DATABASE_URL, min_size=2, max_size=10
            )
            logging.info("API connected to PostgreSQL database")
            break
        except Exception as e:
            if attempt == max_retries - 1:
                logging.error(
                    f"Failed to connect to database after {max_retries} attempts: {e}"
                )
                raise
            logging.warning(
                f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s..."
            )
            await asyncio.sleep(retry_delay)

    # Start consumer thread
    thread = threading.Thread(target=consume_loop, daemon=True)
    thread.start()
    logging.info("Started Kafka consumer thread")

    yield

    # Shutdown
    if api_db_pool:
        await api_db_pool.close()
    if consumer_db_pool:
        await consumer_db_pool.close()
    logging.info("Disconnected from PostgreSQL database")


# FastAPI app setup
app = FastAPI(title="Consumer", version="2.0.0", lifespan=lifespan)


# API Routes
@app.get("/analytics")
async def analytics(limit: int = 10):
    """Returns the most recent processed messages from the database."""
    query = """
        SELECT device_id, metric, value, timestamp, location, 
               anomaly_detected, rolling_avg, deviation_pct, processed_at
        FROM device_readings 
        ORDER BY processed_at DESC 
        LIMIT $1
    """

    async with api_db_pool.acquire() as connection:
        results = await connection.fetch(query, limit)
        messages = [dict(row) for row in results]
    return {"messages": messages}


@app.get("/device-stats")
async def device_statistics():
    """Returns aggregated statistics per device from database."""
    query = """
        SELECT 
            device_id,
            COUNT(*) as message_count,
            AVG(value) as avg_value,
            MAX(processed_at) as last_seen,
            COUNT(CASE WHEN anomaly_detected = true THEN 1 END) as anomaly_count,
            AVG(rolling_avg) as avg_rolling_avg
        FROM device_readings 
        GROUP BY device_id
        ORDER BY last_seen DESC
    """

    async with api_db_pool.acquire() as connection:
        results = await connection.fetch(query)
        stats_summary = {}
        for row in results:
            stats_summary[row["device_id"]] = {
                "message_count": row["message_count"],
                "avg_value": round(float(row["avg_value"]), 2),
                "avg_rolling_avg": round(float(row["avg_rolling_avg"]), 2),
                "last_seen": row["last_seen"].isoformat() if row["last_seen"] else None,
                "anomaly_count": row["anomaly_count"],
            }
    return {"device_stats": stats_summary}


@app.get("/anomalies")
async def recent_anomalies(limit: int = 20):
    """Returns recent messages flagged as anomalies from database."""
    query = """
        SELECT device_id, metric, value, timestamp, location, 
               rolling_avg, deviation_pct, processed_at
        FROM device_readings 
        WHERE anomaly_detected = true
        ORDER BY processed_at DESC 
        LIMIT $1
    """

    async with api_db_pool.acquire() as connection:
        results = await connection.fetch(query)
        anomalies = [dict(row) for row in results]
    return {"anomalies": anomalies}


@app.get("/system-stats")
async def system_statistics():
    """Overall system statistics from database"""
    queries = {
        "total_readings": "SELECT COUNT(*) as count FROM device_readings",
        "unique_devices": "SELECT COUNT(DISTINCT device_id) as count FROM device_readings",
        "total_anomalies": "SELECT COUNT(*) as count FROM device_readings WHERE anomaly_detected = true",
        "latest_reading": "SELECT MAX(processed_at) as latest FROM device_readings",
    }

    stats = {}
    async with api_db_pool.acquire() as connection:
        for key, query in queries.items():
            result = await connection.fetchrow(query)
            if key == "latest_reading":
                stats[key] = result["latest"].isoformat() if result["latest"] else None
            else:
                stats[key] = result["count"] if result else 0

    return stats


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    try:
        async with api_db_pool.acquire() as connection:
            await connection.fetchrow("SELECT 1 as test")
        db_status = "healthy"
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "kafka_consumer": "running",
    }
