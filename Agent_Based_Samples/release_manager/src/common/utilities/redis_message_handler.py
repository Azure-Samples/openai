# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from redis.asyncio import Redis

from common.contracts.common.answer import Answer
from common.contracts.orchestrator.response import Response


class RedisMessageHandler:
    def __init__(
        self,
        session_id: str,
        thread_id: str,
        user_id: str,
        redis_client: Redis,
        redis_message_queue_channel: str,
    ) -> None:
        self.session_id = session_id
        self.thread_id = thread_id
        self.user_id = user_id

        self.redis_client = redis_client
        self.redis_message_queue_channel = redis_message_queue_channel

    async def send_update(self, update_message: str, dialog_id: str = None):
        answer = Answer(answer_string=update_message)
        response = Response(
            session_id=self.session_id,
            dialog_id=dialog_id,
            thread_id=self.thread_id,
            user_id=self.user_id,
            answer=answer,
        )
        await self.redis_client.publish(self.redis_message_queue_channel, response.model_dump_json())

    async def send_final_response(self, response: Response):
        response.session_id = self.session_id
        response.thread_id = self.thread_id
        response.user_id = self.user_id

        await self.redis_client.publish(self.redis_message_queue_channel, response.model_dump_json())
