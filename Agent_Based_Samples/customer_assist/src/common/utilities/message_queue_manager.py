# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List

import asyncio
from redis.asyncio import Redis

from common.telemetry.app_logger import AppLogger


class MessageQueueManager:
    """
    A Redis based Message Queue Handler for publishing and subscribing to messages.
    """

    def __init__(
        self,
        logger: AppLogger,
        redis_host: str,
        redis_port: int,
        redis_password: str,
        redis_ssl: bool,
    ):
        """
        Initialize the MessageQueueHandler with a Redis client.
        """
        self.logger = logger

        self._redis_client = Redis(host=redis_host, port=redis_port, password=redis_password, ssl=redis_ssl)
        self._publish_lock = asyncio.Lock()
        self._subscribers: List[asyncio.Task] = []

    async def publish_async(self, channel, message):
        """
        Publish a message to a message queue.
        """
        try:
            async with self._publish_lock:
                await self._redis_client.publish(channel, message)
                self.logger.info(f"Published message to channel {channel}: {message}")
        except Exception as ex:
            self.logger.error(f"Failed to publish message to channel {channel}: {ex}")
            raise

    async def subscribe_async(self, channels: List[str], on_message_received):
        """
        Asynchronously subscribe to one or more channels and handle incoming messages.

        on_message_received callback is invoked, and all errors are logged but not observed.
        Caller is expected to handle exceptions appropriately.
        """
        try:
            pubsub = self._redis_client.pubsub()
            await pubsub.subscribe(*channels)
            self.logger.info(f"Subscribed to channels: {', '.join(channels)}")

            async def listener():
                while True:
                    try:
                        message = await pubsub.get_message(ignore_subscribe_messages=True)

                        if message is not None:
                            channel = (
                                message["channel"].decode("utf-8")
                                if isinstance(message["channel"], bytes)
                                else message["channel"]
                            )
                            data = (
                                message["data"].decode("utf-8")
                                if isinstance(message["data"], bytes)
                                else message["data"]
                            )

                            self.logger.info(f"Received message from channel {channel}: {data}")
                            await on_message_received(data)
                    except Exception as ex:
                        self.logger.error(f"Error in message_handler: {ex}")

            subscriber_task = asyncio.create_task(listener())
            self._subscribers.append(subscriber_task)
            self.logger.info(f"Started subscriber task for channels {', '.join(channels)}")
            await subscriber_task
        except Exception as ex:
            self.logger.exception(f"Failed to subscribe to channels {', '.join(channels)}: {ex}")
            raise

    async def close_async(self):
        """
        Close the Redis client connection and cancel any subscriber tasks.
        This method is best-effort and does not throw exception.
        """
        try:
            # 1. Cancel all subscriber tasks.
            for task in self._subscribers:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    self.logger.info("Subscriber task cancelled successfully.")

            # 2. Close the Redis client.
            await self._redis_client.close()
            self.logger.info("Redis connection closed successfully.")
        except Exception as ex:
            self.logger.error(f"Failed to close Redis connection: {ex}")
