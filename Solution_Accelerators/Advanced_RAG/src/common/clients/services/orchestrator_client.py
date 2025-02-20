from typing import Tuple
import json

from common.clients.services.client import make_request, HttpMethod
from common.contracts.orchestrator.bot_request import BotRequest
from common.contracts.orchestrator.bot_response import Answer, BotResponse
from common.telemetry.app_logger import AppLogger
from common.utilities.http_response_utils import HTTPStatusCode

class OrchestratorClient():
    def __init__(self, base_uri: str, logger: AppLogger):
        self.base_uri = base_uri
        self.logger = logger
 
    def start(self, start_request: BotRequest) -> Tuple[BotResponse, int]:
        path = "/start"
        payload = start_request.model_dump()
        json_bot_response, bot_response_status_code = make_request(self.base_uri, path, HttpMethod.POST, self.logger, payload, True)
        try:
            bot_response = BotResponse(**json.loads(json_bot_response))
            return bot_response, bot_response_status_code
        except KeyError as e:
            self.logger.error(f"Error parsing bot response: {e}")
            return BotResponse(answer=Answer(), error="An unexpected error occurred."), HTTPStatusCode.INTERNAL_SERVER_ERROR.value