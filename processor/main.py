import logging
import os
from aiokafka import AIOKafkaConsumer
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
INPUT_TOPIC = "iot-sensor-data-validated"
GROUP_ID = "iot-processing-service"


async def process():
    # Initialize consumer
    consumer = AIOKafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
    )
    await consumer.start()

    # Consume messages
    try:
        async for msg in consumer:
            print(
                "consumed: ",
                msg.topic,
                msg.partition,
                msg.offset,
                msg.key,
                msg.value,
                msg.timestamp,
            )
    finally:
        await consumer.stop()


async def main():
    logger.info("IoT Data Processing Service Starting...")
    logger.info(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Input: {INPUT_TOPIC}")

    await process()

    logger.info("IoT Data Processing Service Stopping...")


if __name__ == "__main__":
    asyncio.run(main())
