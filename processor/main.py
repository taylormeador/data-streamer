import logging
import os
from aiokafka import AIOKafkaConsumer
import asyncio
import json
import sys

from db import get_db_pool
from processor_class import Processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")

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
    pool = await get_db_pool(DATABASE_URL, logger)
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
    processor = Processor(consumer, pool, logger)
    await processor.process()

    # Exit gracefully
    pool.close()
    logger.info("IoT Data Processing Service Stopping...")


if __name__ == "__main__":
    asyncio.run(main())
