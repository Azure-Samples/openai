from redis.asyncio import Redis

from common.contracts.orchestrator.bot_response import Answer, BotResponse


class RedisMessagingUtil:
    def __init__(
        self,
        connection_id: str,
        dialog_id: str,
        conversation_id: str,
        user_id: str,
        redis_client: Redis,
        redis_message_queue_channel: str,
    ) -> None:
        self.connection_id = connection_id
        self.dialog_id = dialog_id
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.redis_client = redis_client
        self.redis_message_queue_channel = redis_message_queue_channel
        self.user_id = user_id

    async def send_update(self, update_message: str):
        answer = Answer(answer_string=update_message)
        response = BotResponse(
            connection_id=self.connection_id,
            dialog_id=self.dialog_id,
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            answer=answer,
        )
        await self.redis_client.publish(self.redis_message_queue_channel, response.model_dump_json())

    async def send_bot_response(self, bot_response: BotResponse):
        bot_response.connection_id = self.connection_id
        bot_response.dialog_id = self.dialog_id
        bot_response.conversation_id = self.conversation_id
        bot_response.user_id = self.user_id

        await self.redis_client.publish(self.redis_message_queue_channel, bot_response.model_dump_json())
