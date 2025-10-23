import json
import time
from typing import List
from dataclasses import dataclass
import metrics


@dataclass
class IOTMessage:
    key: str
    value: dict


def validate_batch(message_batch, logger):
    """Validate incoming IoT message batch. Logs and discards invalid messages."""

    start_time = time.time()
    validated_messages = []

    for message in message_batch:
        logger.info(f"validating message with key {message.key}")

        # Decode to JSON
        try:
            data = json.loads(message.value.decode("utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"Unable to parse message to JSON: {e}")
            metrics.messages_rejected.labels(reason="invalid_json").inc()
            continue

        # Required fields
        required_fields = ["device_id", "metric", "value", "timestamp"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            logger.error(f"message missing required fields: {missing_fields}")
            metrics.messages_rejected.labels(reason="missing_fields").inc()
            continue

        # Validate device_id format
        if not isinstance(data["device_id"], str) or not data["device_id"].startswith(
            "device_"
        ):
            logger.error("Invalid device_id format")
            metrics.messages_rejected.labels(reason="invalid_device_id").inc()
            continue

        # Validate metric
        valid_metrics = [
            "temperature",
            "humidity",
            "pressure",
            "vibration",
            "voltage",
            "status",
        ]
        if data["metric"] not in valid_metrics:
            logger.error(f"Invalid metric: {data['metric']}")
            metrics.messages_rejected.labels(reason="invalid_metric").inc()
            continue

        # Validate value is numeric
        try:
            value = float(data["value"])
            if value < -100 or value > 1000:
                logger.error(f"Value out of range: {value}")
                metrics.messages_rejected.labels(reason="value_out_of_range").inc()
                continue
        except (ValueError, TypeError):
            logger.error("Value must be numeric")
            metrics.messages_rejected.labels(reason="non_numeric_value").inc()
            continue

        # Validate timestamp (accept Unix timestamp as float or int)
        try:
            timestamp = float(data["timestamp"])
            # Sanity check: timestamp should be reasonable (between 2020 and 2030)
            if timestamp < 1577836800 or timestamp > 1893456000:
                logger.error(f"Timestamp out of reasonable range: {timestamp}")
                metrics.messages_rejected.labels(reason="invalid_timestamp").inc()
                continue
        except (ValueError, TypeError):
            logger.error("Timestamp must be numeric (Unix timestamp)")
            metrics.messages_rejected.labels(reason="non_numeric_timestamp").inc()
            continue

        # Message is valid
        message = IOTMessage(key=message.key, value=data)
        validated_messages.append(message)
        metrics.messages_validated.inc()

    # Track validation duration
    duration = time.time() - start_time
    metrics.validation_duration.observe(duration)

    return validated_messages


def enrich_batch(message_batch: List[IOTMessage]) -> List[IOTMessage]:
    """Add ingestion timestamp."""

    start_time = time.time()

    # TODO add some kind of compute intensive task here
    for message in message_batch:
        message.value["ingestion_timestamp"] = time.time()

    # Track enrichment duration
    duration = time.time() - start_time
    metrics.enrichment_duration.observe(duration)

    return message_batch
