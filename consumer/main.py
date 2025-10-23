import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import logging
import os
import json
import time
from prometheus_client import start_http_server

import data
import metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
GROUP_ID = "iot-ingestion-service"
TRANSACTIONAL_ID = "transactional-id"
INPUT_TOPIC = "iot-sensor-data"
OUTPUT_TOPIC = "iot-sensor-data-validated"

POLL_TIMEOUT = 60 * 1000

METRICS_PORT = int(os.getenv("METRICS_PORT", "8000"))


def serializer(data: dict):
    return json.dumps(data).encode("utf-8")


async def main():
    # Start Prometheus metrics server
    start_http_server(METRICS_PORT)
    logger.info(f"Metrics server started on port {METRICS_PORT}")

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

                # Collect all messages from batch
                for topic, messages in message_batch.items():
                    input_messages.extend(messages)
                    commit_offsets[topic] = messages[-1].offset + 1
                    metrics.kafka_messages_consumed.labels(topic=topic).inc(
                        len(messages)
                    )

                # Track batch size
                batch_size = len(input_messages)
                metrics.batch_size.observe(batch_size)
                metrics.messages_in_flight.set(batch_size)

                logger.info(f"Processing batch of {batch_size} messages")

                # Validate + enrich messages
                validated_messages = data.validate_batch(input_messages, logger)
                output_messages = data.enrich_batch(validated_messages)

                logger.info(f"Publishing {len(output_messages)} validated messages")

                # Publish messages
                for message in output_messages:
                    publish_start = time.time()

                    try:
                        logger.debug(f"sending message with key {message.key}")
                        await producer.send(
                            OUTPUT_TOPIC,
                            value=message.value,
                            key=message.key,
                        )

                        # Track successful publish
                        metrics.kafka_messages_published.labels(
                            topic=OUTPUT_TOPIC
                        ).inc()

                        # Track publish duration
                        publish_duration = time.time() - publish_start
                        metrics.kafka_publish_duration.observe(publish_duration)

                    except Exception as e:
                        logger.error(f"Failed to publish message: {e}")
                        metrics.kafka_publish_errors.labels(topic=OUTPUT_TOPIC).inc()
                        raise

                # Commit offsets + clear gauge
                await producer.send_offsets_to_transaction(commit_offsets, GROUP_ID)
                metrics.messages_in_flight.set(0)

                logger.info(
                    f"Batch complete: {len(validated_messages)}/{batch_size} messages validated"
                )

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise
    finally:
        await consumer.stop()
        await producer.stop()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
