from typing import Tuple
import json

from common.clients.services.client import make_request_async, HttpMethod
from common.contracts.skills.search.api_models import SearchRequest, SearchResponse, SearchScenario
from common.telemetry.app_logger import AppLogger
from common.utilities.http_response_utils import HTTPStatusCode

class SearchClient():
    def __init__(self, base_uri: str, logger: AppLogger):
        self.base_uri = base_uri
        self.logger = logger

    async def perform_rag_search(self, search_request: SearchRequest) -> Tuple[SearchResponse, int]:
        path = f"/search?scenario={SearchScenario.RAG.value}"
        
        payload = search_request.model_dump()
        self.logger.info(f"SearchClient.perform_rag_search: Making Post call to: {self.base_uri}{path} Payload: {json.dumps(payload)}")
        json_search_response, search_response_status_code = await make_request_async(self.base_uri, path, HttpMethod.POST, self.logger, payload, True)
        try:
            if search_response_status_code == 200:
                search_response = SearchResponse.model_validate_json(json_search_response)
                return search_response, search_response_status_code
            else:
                return None, search_response_status_code
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing search response. Response: {json_search_response}. Error: {e}")
            return None, HTTPStatusCode.INTERNAL_SERVER_ERROR.value
    
    async def perform_retail_search(self, search_request: SearchRequest) -> Tuple[SearchResponse, int]:
        path = f"/search?scenario={SearchScenario.RETAIL.value}"
        
        payload = search_request.model_dump()
        self.logger.info(f"SearchClient.perform_retail_search: Making Post call to: {self.base_uri}{path} Payload: {json.dumps(payload)}")
        json_search_response, search_response_status_code = await make_request_async(self.base_uri, path, HttpMethod.POST, self.logger, payload, True)
        try:
            if search_response_status_code == HTTPStatusCode.OK.value:
                search_response = SearchResponse.model_validate_json(json_search_response)
                return search_response, search_response_status_code
            else:
                return None, search_response_status_code
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing search response. Response: {json_search_response}. Error: {e}")
            return None, HTTPStatusCode.INTERNAL_SERVER_ERROR.value