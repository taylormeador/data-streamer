from confluent_kafka import Consumer, Producer, KafkaError
import logging
import os
import json
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
INPUT_TOPIC = "iot-sensor-data"
OUTPUT_TOPIC = "iot-sensor-data-validated"


def validate_message(message_data: dict) -> tuple[bool, str]:
    """
    Validate incoming IoT message.
    Returns (is_valid, error_message)
    """
    # Required fields
    required_fields = ["device_id", "metric", "value", "timestamp"]
    for field in required_fields:
        if field not in message_data:
            return False, f"Missing required field: {field}"

    # Validate device_id format
    if not isinstance(message_data["device_id"], str) or not message_data[
        "device_id"
    ].startswith("device_"):
        return False, "Invalid device_id format"

    # Validate metric
    valid_metrics = [
        "temperature",
        "humidity",
        "pressure",
        "vibration",
        "voltage",
        "status",
    ]
    if message_data["metric"] not in valid_metrics:
        return False, f"Invalid metric: {message_data['metric']}"

    # Validate value is numeric
    try:
        value = float(message_data["value"])
        if value < -100 or value > 1000:
            return False, f"Value out of range: {value}"
    except (ValueError, TypeError):
        return False, "Value must be numeric"

    # Validate timestamp (accept Unix timestamp as float or int)
    try:
        timestamp = float(message_data["timestamp"])
        # Sanity check: timestamp should be reasonable (between 2020 and 2030)
        if timestamp < 1577836800 or timestamp > 1893456000:  # 2020-01-01 to 2030-01-01
            return False, f"Timestamp out of reasonable range: {timestamp}"
    except (ValueError, TypeError):
        return False, "Timestamp must be numeric (Unix timestamp)"

    return True, ""


def main():
    logger.info("IoT Data Ingestion Service Starting...")
    logger.info(f"Kafka: {KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Input: {INPUT_TOPIC} → Output: {OUTPUT_TOPIC}")

    # Initialize consumer
    consumer = Consumer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "group.id": "iot-ingestion-service",
            "auto.offset.reset": "latest",
            "enable.auto.commit": True,
        }
    )

    # Initialize producer
    producer = Producer(
        {
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "linger.ms": 10,
            "compression.type": "snappy",
        }
    )

    consumer.subscribe([INPUT_TOPIC])
    logger.info("Ready to process messages")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    logger.error(f"Consumer error: {msg.error()}")
                continue

            try:
                message_data = json.loads(msg.value().decode("utf-8"))

                # Validate
                is_valid, error_msg = validate_message(message_data)

                if is_valid:
                    # Add ingestion timestamp
                    message_data["ingestion_timestamp"] = time.time()

                    # Forward to validated topic
                    logger.info(f'Valid message from {message_data["device_id"]}')
                    producer.produce(
                        OUTPUT_TOPIC,
                        key=message_data["device_id"].encode("utf-8"),
                        value=json.dumps(message_data).encode("utf-8"),
                    )
                    producer.poll(0)  # Trigger callbacks
                else:
                    logger.warning(
                        f"Invalid message from {message_data.get('device_id', 'unknown')}: {error_msg}"
                    )

            except json.JSONDecodeError:
                logger.error("Failed to decode message as JSON")
            except Exception as e:
                logger.error(f"Error processing message: {e}")

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        producer.flush()
        consumer.close()
        logger.info("Shutdown complete")


if __name__ == "__main__":
    main()
