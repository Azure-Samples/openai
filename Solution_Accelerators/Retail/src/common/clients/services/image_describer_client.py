from common.clients.services.client import make_request_async, HttpMethod

from common.contracts.skills.image_describer.api_models import AnalysisRequest, AnalysisResponse 
from common.utilities.http_response_utils import HTTPStatusCode
from common.telemetry.app_logger import AppLogger
from typing import Tuple

class ImageDescriberClient():
    def __init__(self, base_uri: str, logger: AppLogger):
        self.base_uri = base_uri
        self.logger = logger

    async def analyze(self, analysis_request: AnalysisRequest) -> Tuple[AnalysisResponse, int]:
        path = f"/analyze"
        payload = analysis_request.model_dump()
        json_analyze_response, analysis_response_status_code = await make_request_async(self.base_uri, path, HttpMethod.POST, self.logger, payload, True)
        try:
            if analysis_response_status_code == 200:
                analysis_response = AnalysisResponse.model_validate_json(json_analyze_response)
                return analysis_response, analysis_response_status_code
            else:
                return None, analysis_response_status_code
        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing analysis response: {e}")
            return None, HTTPStatusCode.INTERNAL_SERVER_ERROR.value