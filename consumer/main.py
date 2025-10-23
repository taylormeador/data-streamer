import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import os
import json

import data
from shared.elk_logging import setup_logging

logger = setup_logging("producer-service")

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
GROUP_ID = "iot-ingestion-service"
TRANSACTIONAL_ID = "transactional-id"
INPUT_TOPIC = "iot-sensor-data"
OUTPUT_TOPIC = "iot-sensor-data-validated"

POLL_TIMEOUT = 60 * 1000


def serializer(data: dict):
    return json.dumps(data).encode("utf-8")


async def main():
    logger.info("IoT Data Ingestion Service Starting...")
    logger.info(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Input: {INPUT_TOPIC} → Output: {OUTPUT_TOPIC}")

    # Initialize consumer
    consumer = AIOKafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        enable_auto_commit=False,
        group_id=GROUP_ID,
        isolation_level="read_committed",
    )
    await consumer.start()

    # Initialize producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        transactional_id=TRANSACTIONAL_ID,
        value_serializer=serializer,
    )
    await producer.start()

    logger.info("Ready to process messages")

    try:
        while True:
            message_batch = await consumer.getmany(timeout_ms=POLL_TIMEOUT)
            if not message_batch:
                # This just creates an infinite loop instead of crashing.
                # In a real system we could check for interrupt or send heartbeat or whatever else here.
                logger.debug("No messages received, continuing...")
                continue

            async with producer.transaction():
                commit_offsets = {}
                input_messages = []

                for topic, messages in message_batch.items():
                    input_messages.extend(messages)
                    commit_offsets[topic] = messages[-1].offset + 1

                validated_messages = data.validate_batch(input_messages, logger)
                output_messages = data.enrich_batch(validated_messages)
                for message in output_messages:
                    logger.info(f"sending message with key {message.key}")
                    await producer.send(
                        OUTPUT_TOPIC,
                        value=message.value,
                        key=message.key,
                    )

                await producer.send_offsets_to_transaction(commit_offsets, GROUP_ID)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await consumer.stop()
        await producer.stop()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
