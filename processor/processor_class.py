# pyright: reportOptionalSubscript=false

import logging
from aiokafka import AIOKafkaConsumer
import asyncpg
import asyncio


class Processor:
    def __init__(
        self,
        consumer: AIOKafkaConsumer,
        max_tasks: int,
        num_workers: int,
        db_pool: asyncpg.Pool,
        max_conns: int,
        logger: logging.Logger,
    ):
        self._consumer = consumer
        self._queue = asyncio.Queue(max_tasks)
        self._num_workers = num_workers
        self._workers = []
        self._db_pool = db_pool
        self._db_semaphore = asyncio.Semaphore(max_conns)
        self._logger = logger

    async def start(self):
        """Init workers and enter loop."""
        for i in range(self._num_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)

        await self._consume_loop()

    async def _shutdown(self):
        """Graceful shutdown."""
        pass

    async def _consume_loop(self):
        """Read from Kafka and put on queue."""
        try:
            async for msg in self._consumer:
                await self._queue.put(msg)
        finally:
            await self._consumer.stop()

    async def _process_message(self, msg):
        """Insert message into database."""
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
            async with self._db_semaphore:  # Limit number of db conns to avoid exhausting pool
                async with self._db_pool.acquire() as connection:
                    await connection.execute(query, *values)
            self._logger.info(f"Stored reading for device {msg_values['device_id']}")
        except Exception as e:
            self._logger.error(f"Failed to store reading: {e}")
            raise

    async def _worker(self, worker_id: int):
        """Init worker and pull from queue in loop."""
        self._logger.info(f"Starting worker #{worker_id}...")
        while True:
            msg = await self._queue.get()
            if msg is None:
                break

            try:
                await self._process_message(msg)
            except Exception as e:
                self._logger.error(f"Worker #{worker_id}: Error processing: {e}")
            finally:
                self._queue.task_done()

        # TODO This never happens for now.
        # Consider implementing this by sending a specific payload
        # from the "device" layer in order to sync system wide shutdown.
        self._logger.info(f"Worker #{worker_id} found poison pill, exiting...")
        await self._shutdown()
