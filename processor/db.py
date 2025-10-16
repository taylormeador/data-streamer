import asyncpg
import asyncio
import logging


async def get_db_pool(dsn: str, logger: logging.Logger) -> asyncpg.Pool:
    max_retries = 3
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            db_pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)
            return db_pool

        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(
                    f"Failed to connect to database after {max_retries} attempts: {e}"
                )
                raise
            logger.warning(
                f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s..."
            )
            await asyncio.sleep(retry_delay)

    raise RuntimeError("Exhausted all retry attempts without connecting to database")
