import json
import time
from typing import List
from dataclasses import dataclass


@dataclass
class IOTMessage:
    key: str
    value: dict


def validate_batch(message_batch, logger):
    """Validate incoming IoT message batch. Logs and discards invalid messages."""

    # TODO send the invalid messages to DLQ topic
    validated_messages = []
    for message in message_batch:
        logger.info(f"validating message with key {message.key}")

        # Decode to JSON
        try:
            data = json.loads(message.value.decode("utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"Unable to parse message to JSON: {e}")
            continue

        # Required fields
        required_fields = ["device_id", "metric", "value", "timestamp"]
        for field in required_fields:
            if field not in data:
                logger.error("message missing required field")
                continue

        # Validate device_id format
        if not isinstance(data["device_id"], str) or not data["device_id"].startswith(
            "device_"
        ):
            logger.error("Invalid device_id format")
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
            continue

        # Validate value is numeric
        try:
            value = float(data["value"])
            if value < -100 or value > 1000:
                logger.error(f"Value out of range: {value}")
                continue

        except (ValueError, TypeError):
            logger.error("Value must be numeric")
            continue

        # Validate timestamp (accept Unix timestamp as float or int)
        try:
            timestamp = float(data["timestamp"])
            # Sanity check: timestamp should be reasonable (between 2020 and 2030)
            if timestamp < 1577836800 or timestamp > 1893456000:
                logger.error(f"Timestamp out of reasonable range: {timestamp}")
                continue
        except (ValueError, TypeError):
            logger.error("Timestamp must be numeric (Unix timestamp)")
            continue

        message = IOTMessage(key=message.key, value=data)
        validated_messages.append(message)

    return validated_messages


def enrich_batch(message_batch: List[IOTMessage]) -> List[IOTMessage]:
    """Add ingestion timestamp."""

    # TODO add some kind of compute intensive task here
    # TODO this is dumb
    for message in message_batch:
        message.value["ingestion_timestamp"] = time.time()

    return message_batch
