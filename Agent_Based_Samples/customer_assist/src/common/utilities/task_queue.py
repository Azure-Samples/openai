# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from redis.asyncio import Redis
from tenacity import retry, stop_after_attempt, wait_fixed

from common.telemetry.app_logger import AppLogger


class TaskQueue:
    """
    A Redis based Task Queue.
    """

    def __init__(
        self,
        logger: AppLogger,
        queue_name: str,
        redis_host: str,
        redis_port: int,
        redis_password: str,
        redis_ssl: bool,
    ):
        self.logger = logger
        self.queue_name = queue_name

        self.redis = Redis(
            host=redis_host, port=redis_port, password=redis_password, ssl=redis_ssl
        )

    @retry(reraise=True, stop=stop_after_attempt(3), wait=wait_fixed(0.5))
    async def enqueue(self, task):
        """Add a task to the queue."""
        try:
            await self.redis.rpush(self.queue_name, task)
            self.logger.info(f"Task enqueued successfully.")
        except Exception as ex:
            self.logger.error(f"Error enqueuing task: {ex}")
            raise

    async def dequeue(self):
        """Remove and return a task from the queue."""
        try:
            if not await self.is_empty():
                return await self.redis.lpop(self.queue_name)

            return None
        except Exception as ex:
            self.logger.error(f"Error dequeuing task: {ex}")
            raise

    async def size(self) -> int:
        """Get the current size of the queue."""
        try:
            return await self.redis.llen(self.queue_name)
        except Exception as ex:
            self.logger.error(f"Error getting queue size: {ex}")
            raise

    async def is_empty(self) -> bool:
        """Check if the queue is empty."""
        size = await self.size()
        return size == 0

    async def clear(self) -> None:
        """Clear all tasks from the queue."""
        try:
            await self.redis.delete(self.queue_name)
            self.logger.info("Queue cleared")
        except Exception as ex:
            self.logger.error(f"Error clearing queue: {ex}")
            raise

    async def close(self):
        """Close the Task Queue connection."""
        try:
            await self.redis.close(close_connection_pool=True)
            self.logger.info("Task queue connection closed successfully.")
        except Exception as ex:
            self.logger.error(f"Error closing Task queue connections: {ex}")
            raise
