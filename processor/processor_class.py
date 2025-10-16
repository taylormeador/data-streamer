# pyright: reportOptionalSubscript=false

import logging
from aiokafka import AIOKafkaConsumer
import asyncpg


class Processor:
    def __init__(
        self,
        consumer: AIOKafkaConsumer,
        db_pool: asyncpg.Pool,
        logger: logging.Logger,
    ):
        self._consumer = consumer
        self._db_pool = db_pool
        self._logger = logger

    async def process(self):
        try:
            async for msg in self._consumer:
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
                    async with self._db_pool.acquire() as connection:
                        await connection.execute(query, *values)
                    self._logger.info(
                        f"Stored reading for device {msg_values['device_id']}"
                    )
                except Exception as e:
                    self._logger.error(f"Failed to store reading: {e}")
                    raise

        finally:
            await self._consumer.stop()
