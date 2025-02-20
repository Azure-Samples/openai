from app.utils.messaging_utils import RedisMessagingUtil

from common.contracts.orchestrator.bot_response import BotResponse


class RequestManager:
    async def emit_update(self, update_string: str) -> None:
        """Emits update from the orchestrator."""
        pass

    async def emit_final_answer(self, start_response: BotResponse) -> None:
        """Emits final answer from the orchestrator."""
        pass


class MessageQueueRequestManager(RequestManager):
    def __init__(self, redis_messaging_util: RedisMessagingUtil) -> None:
        self.redis_messaging_util = redis_messaging_util

    async def emit_update(self, update_message: str) -> None:
        await self.redis_messaging_util.send_update(update_message)

    async def emit_final_answer(self, bot_response: BotResponse) -> None:
        await self.redis_messaging_util.send_bot_response(bot_response)


class HTTPRequestManager(RequestManager):
    def __init__(self) -> None:
        self.update_message_list = []
        self.final_answer_json = {}

    async def emit_update(self, update_message: str) -> None:
        self.update_message_list.append(update_message)

    async def emit_final_answer(self, bot_response: BotResponse) -> None:
        self.final_answer_json = bot_response.model_dump()
        return self.final_answer_json
