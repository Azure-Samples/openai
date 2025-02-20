from enum import Enum
from redis.asyncio import Redis
from tenacity import retry, stop_after_attempt, wait_fixed

from common.telemetry.app_logger import AppLogger

class TaskStatus(str, Enum):
    ENQUEUED = "Enqueued"
    PROCESSING = "Processing"
    PROCESSED = "Processed"
    FAILED = "Failed"
    NOT_FOUND = "Not Found"

class TaskStatusManager:
    """
    A Redis based Task Status Manager.
    """
    def __init__(self, logger: AppLogger, task_status_map_name: str, redis_host: str, redis_port: int, redis_password: str, redis_ssl: bool):
        self.logger = logger
        self.task_status_map_name = task_status_map_name

        self.redis = Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            ssl=redis_ssl
        )

        self.in_progress_tasks = {}

    async def set_task_status(self, task_id, message, status):
        """ Set the status of a task."""
        try:
            await self.redis.hset(self.task_status_map_name, task_id, message)
            await self.update_in_progress_tasks(task_id, status)
            self.logger.info(f"Task status updated successfully.")
        except Exception as ex:
            self.logger.error(f"Error updating task status: {ex}")
            raise

    async def get_task_status(self, task_id):
        """ Get the status of a task."""
        try:
            if await self.redis.hexists(self.task_status_map_name, task_id):
                task_status = await self.redis.hget(self.task_status_map_name, task_id)
                return task_status.decode('utf-8')
            return TaskStatus.NOT_FOUND
        except Exception as ex:
            self.logger.error(f"Error getting task status: {ex}")
            raise

    async def update_in_progress_tasks(self, task_id, status):
        """Update the list of in progress tasks."""
        try:
            if status == TaskStatus.ENQUEUED:
                return
            elif status == TaskStatus.PROCESSING:
                self.in_progress_tasks[task_id] = status
            elif task_id in self.in_progress_tasks:
                del self.in_progress_tasks[task_id]
        except Exception as ex:
            self.logger.error(f"Error updating in progress tasks: {ex}")
            raise

    async def remove_in_progress_tasks(self):
        """ Remove in progress tasks in case of disconnection. """
        try:
            for task_id in self.in_progress_tasks:
                await self.redis.hdel(self.task_status_map_name, task_id)
            self.logger.info("In Progress tasks removed from hash.")
        except Exception as ex:
            self.logger.error(f"Error removing in progress tasks from hash: {ex}")
            raise