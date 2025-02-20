import requests
from requests.auth import AuthBase
from common.telemetry.app_logger import AppLogger
from datetime import datetime
from enum import Enum
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Optional, Tuple, Dict

class HTTPClient:
    class HttpMethod(Enum):
        POST="POST"
        GET="GET"
        PUT="PUT"
        DELETE="DELETE"

    def __init__(self, base_uri: str, logger: AppLogger):
        self.base_uri = base_uri
        self.logger = logger

    @retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=60))
    def make_request(self, path: str, method: HttpMethod, payload: Optional[dict] = None, 
            raise_for_status_code: bool = True, auth: Optional[AuthBase] = None, custom_headers: Optional[Dict] = {}) -> Tuple[str, int]:
        
        # Merge any custom headers with the base properties
        headers = self.logger.get_base_properties() | custom_headers

        self.logger.info(f"Making {method.value} request to {path} endpoint")
        start_time = datetime.now()

        try:
            response: requests.Response
            request_params = {
                "url": self.base_uri + path,
                "headers": headers
            }

            if auth is not None:
                request_params["auth"] = auth

            if payload is not None:
                request_params["json"] = payload

            if method == self.HttpMethod.POST:
                response = requests.post(**request_params)
            elif method == self.HttpMethod.GET:
                response = requests.get(**request_params)
            elif method == self.HttpMethod.PUT:
                response = requests.put(**request_params)
            elif method == self.HttpMethod.DELETE:
                response = requests.delete(**request_params)
            else:
                raise Exception(f"Invalid HTTP method: {method.value}")
            end_time = datetime.now()

            addl_dimension = {
                "sessionDB_request_time[MS]": (end_time - start_time).total_seconds() * 1000
            }

            if raise_for_status_code:
                response.raise_for_status()
            self.logger.info(f"Received response from {path} endpoint", properties=addl_dimension)
            return response.text, response.status_code
        except requests.RequestException as re:
            self.logger.error(f"Error making {method.value} request to {path} endpoint: {str(re)}")
            raise re