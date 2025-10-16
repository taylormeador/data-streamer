import logging
import os
import asyncio
import json
import sys

from aiokafka import AIOKafkaConsumer
from prometheus_client import start_http_server

from db import get_db_pool
from processor_class import Processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")
MAX_CONNS = 50  # Postgres default is 100 total conns, allow 50 for the processor.
NUM_WORKERS = 75  # 50 db conns + a few workers in the CPU at any given time.
MAX_TASKS = 1000  # Limit the number of Kafka messages in memory.
METRICS_PORT = int(os.getenv("METRICS_PORT", 8080))

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
INPUT_TOPIC = "iot-sensor-data-validated"
GROUP_ID = "iot-processing-service"


def deserializer(serialized):
    return json.loads(serialized)


async def main():
    logger.info("IoT Data Processing Service Starting...")
    logger.info(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Input: {INPUT_TOPIC}")

    # Connect to db
    if not DATABASE_URL:
        logger.fatal("DATABASE_URL not found")
        sys.exit(1)
    try:
        pool = await get_db_pool(DATABASE_URL, logger)
        logger.info("Connected to database")
    except Exception as e:
        logger.fatal(f"Unable to connect to database: {e}")

    # Start prometheus server
    start_http_server(METRICS_PORT)

    # Init consumer
    consumer = AIOKafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        value_deserializer=deserializer,
    )
    await consumer.start()

    # Enter processing loop
    processor = Processor(consumer, MAX_TASKS, NUM_WORKERS, pool, MAX_CONNS, logger)  # type: ignore
    await processor.start()

    # Exit gracefully
    await pool.close()  # type: ignore
    logger.info("IoT Data Processing Service Stopping...")


if __name__ == "__main__":
    asyncio.run(main())
