# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from typing import Optional
from common.telemetry.app_logger import AppLogger
from common.utilities.task_queue import TaskQueue


class TaskQueueManager:
    """
    Handles the underlying task queue by providing ability to submit tasks, and start task processing.
    """

    def __init__(
        self,
        logger: AppLogger,
        queue_name: str,
        redis_host: str,
        redis_port: int,
        redis_password: str,
        redis_ssl: bool,
        max_worker_threads: Optional[int] = None,
    ):
        self.logger = logger
        self.max_worker_threads = max_worker_threads

        # Setup task queue for processing tasks.
        self._task_queue = TaskQueue(
            logger=logger,
            queue_name=queue_name,
            redis_host=redis_host,
            redis_port=redis_port,
            redis_password=redis_password,
            redis_ssl=redis_ssl,
        )

        self._processing_event = asyncio.Event()

    async def submit_task(self, task_payload):
        """
        Submit a task to the task queue.
        """
        if not self._task_queue:
            self.logger.error("Task Manager: Task queue is not initialized.")
            raise Exception(
                "Task queue must be initialized before task submission. Create TaskManager first."
            )

        await self._task_queue.enqueue(task_payload)
        self.logger.info(f"Task Manager: task payload submitted.")

    async def start_async(self, on_task_payload_received):
        """
        Process tasks from the task queue.
        on_task_payload_received is invoked with the payload.
        """
        # Set flag before processing tasks.
        self._processing_event.set()
        self.logger.info("Task Manager started.")

        (
            await asyncio.gather(
                *(
                    self.__task_worker(on_task_payload_received)
                    for _ in range(self.max_worker_threads)
                )
            )
            if self.max_worker_threads
            else await self.__task_worker(on_task_payload_received)
        )

    async def __task_worker(self, on_task_payload_received):
        self.logger.info("Starting task worker..")
        try:
            while self._processing_event.is_set():
                task_payload = await self._task_queue.dequeue()

                if task_payload:
                    self.logger.info(
                        f"Task Manager: found task payload for processing."
                    )

                    # Create task processor instance and invoke task processor endpoint.
                    await on_task_payload_received(task_payload)

                    self.logger.info(f"Task Manager: task processed successfully!")
                else:
                    await asyncio.sleep(1)  # Wait before checking again
        except Exception as ex:
            self.logger.error(f"Task Manager: Error processing jobs: {ex}.")
            raise

    def stop(self):
        """
        Stop processing jobs.
        """
        self._processing_event.clear()
        self.logger.info("Task Manager: stopped processing tasks.")

    async def get_current_size(self):
        """
        Get the current size of the task queue.
        """
        return await self._task_queue.size()

    async def clear(self):
        """
        Clear all jobs from the task queue.
        """
        await self._task_queue.clear()

    async def close_async(self):
        """
        Closes task manager and associated resources.
        """
        try:
            await self._task_queue.close()
            self.logger.info("Task Manager: task processing closed successfully.")
        except Exception as ex:
            self.logger.error(f"Error closing Task Manager: {ex}")
            raise
