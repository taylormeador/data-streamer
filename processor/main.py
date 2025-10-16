import logging
import os
from aiokafka import AIOKafkaConsumer
import asyncio
import json
import asyncpg
import sys

import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
INPUT_TOPIC = "iot-sensor-data-validated"
GROUP_ID = "iot-processing-service"


def deserializer(serialized):
    return json.loads(serialized)


async def process(consumer: AIOKafkaConsumer, pool: asyncpg.Pool):
    """Asyncronously reads messages from Kafka topic."""
    # Consume messages
    try:
        async for msg in consumer:
            query = """
                INSERT INTO device_readings (
                    device_id,
                    metric,
                    value,
                    timestamp,
                    ingestion_timestamp,
                    message_id,
                    location,
                    processed_at
                ) VALUES (
                    $1, $2, $3, to_timestamp($4),
                    to_timestamp($5), $6::uuid, $7, NOW()
                )
            """

            msg_values = msg.value
            values = (
                msg_values["device_id"],
                msg_values["metric"],
                msg_values["value"],
                msg_values["timestamp"],
                msg_values["ingestion_timestamp"],
                msg_values["message_id"],
                msg_values["location"],
            )

            try:
                async with pool.acquire() as connection:
                    await connection.execute(query, *values)
                logger.info(f"Stored reading for device {msg_values['device_id']}")
            except Exception as e:
                logger.error(f"Failed to store reading: {e}")
                raise

    finally:
        await consumer.stop()


async def main():
    logger.info("IoT Data Processing Service Starting...")
    logger.info(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Input: {INPUT_TOPIC}")

    # Connect to db
    if not DATABASE_URL:
        logger.fatal("DATABASE_URL not found")
        sys.exit(1)
    pool = await db.get_db_pool(DATABASE_URL, logger)
    logger.info("Connected to database")

    # Init consumer
    consumer = AIOKafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        value_deserializer=deserializer,
    )
    await consumer.start()

    # Enter read loop
    await process(consumer, pool)

    pool.close()

    logger.info("IoT Data Processing Service Stopping...")


if __name__ == "__main__":
    asyncio.run(main())
