from common.clients.services.client import make_request_async, HttpMethod
from common.telemetry.app_logger import AppLogger
from common.utilities.http_response_utils import HTTPStatusCode
import json

class ConfigServiceClient():
    def __init__(self, base_uri: str, logger: AppLogger):
        self.base_uri = base_uri
        self.logger = logger

    async def get_config(self, config_id, config_version):
        path = f"/configuration-service/configs/{config_id}/{config_version}"

        self.logger.info(f"ConfigHub.get_config: Making Post call to: {self.base_uri}{path}")

        json_config_response, status_code = await make_request_async(self.base_uri, path, HttpMethod.GET, self.logger, True)
        try:
            if status_code != 200:
                self.logger.error(f"Error fetching configuration. Response: {json_config_response}, status_code: {status_code}")
                json_config_response = None
            else:
                json_config_response = json.loads(json_config_response)

            return json_config_response, status_code

        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing config_hub response. Response: {json_config_response}. Error: {e}")
            return None, HTTPStatusCode.INTERNAL_SERVER_ERROR.value