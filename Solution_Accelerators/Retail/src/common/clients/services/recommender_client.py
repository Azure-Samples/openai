from common.clients.services.client import make_request_async, HttpMethod

from common.contracts.skills.recommender.api_models import RecommenderRequest, RecommenderResponse
from common.utilities.http_response_utils import HTTPStatusCode
from common.telemetry.app_logger import AppLogger
from typing import Tuple
import json

class RecommenderClient():
    def __init__(self, base_uri: str, logger: AppLogger):
        self.base_uri = base_uri
        self.logger = logger

    async def recommend(self, recommender_request: RecommenderRequest) -> Tuple[RecommenderResponse, int]:
        path = f"/recommend"
        payload = recommender_request.model_dump()
        self.logger.info(f"RecommenderClient.recommend: Making Post call to: {self.base_uri}{path} Payload: {json.dumps(payload)}")
        json_recommender_response, recommender_response_status_code = await make_request_async(self.base_uri, path, HttpMethod.POST, self.logger, payload, True)
        try:
            if recommender_response_status_code == 200:
                recommender_response = RecommenderResponse.model_validate_json(json_recommender_response)
                return recommender_response, recommender_response_status_code
            else:
                return None, recommender_response_status_code
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing recommender response: Response: {recommender_response}. Error: {e}")
            return None, HTTPStatusCode.INTERNAL_SERVER_ERROR.value