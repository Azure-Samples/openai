# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import aiohttp
import json
import time
import requests

from common.telemetry.app_logger import AppLogger
from common.telemetry.log_classes import HttpRequestLog
from enum import Enum
from typing import Optional, Tuple

class HttpMethod(Enum):
    POST = "POST"
    GET = "GET"
    PUT = "PUT"
    DELETE = "DELETE"

def make_request(base_uri: str, path: str, method: HttpMethod, logger: AppLogger, 
                 payload: Optional[dict] = None, raise_for_status_code: bool = True) -> Tuple[str, int]:
    
    logger.info(f"Making {method.value} request to {path} endpoint")

    url = base_uri + path

    try:
        log_properties = HttpRequestLog()
        response = requests.request(method.value, url=url, headers={}, json=payload)
        if raise_for_status_code:
            response.raise_for_status()
        response_status = response.status_code
        response_text = response.text
        log_properties.request_url = url
        log_properties.method = method.value
        log_properties.request = json.dumps(payload)
        log_properties.response = response_text
        log_properties.status_code = response_status
        log_properties.record_duration_ms()

        logger.info("Http call", properties=log_properties.model_dump())

        return response_text, response_status
    except Exception as re:
        logger.error(f"Error making {method.value} request to {path} endpoint: {str(re)}")
        raise

async def make_request_async(base_uri: str, path: str, method: HttpMethod, logger: AppLogger, 
                             payload: Optional[dict] = None, raise_for_status_code: bool = True) -> Tuple[str, int]:
    logger.info(f"Making {method.value} request to {path} endpoint")

    url = base_uri + path

    try:
        log_properties = HttpRequestLog()
        async with aiohttp.ClientSession() as session:
            async with session.request(method.value, url=url, headers={}, json=payload) as response:
                # if raise_for_status_code: ## removing forcing raise for status code as that will throw an exception and then session might not be closed
                #     response.raise_for_status()
                response_status = response.status
                response_text = await response.text()
        
        log_properties.request_url = url
        log_properties.method = method.value
        log_properties.request = json.dumps(payload)
        log_properties.response = response_text
        log_properties.status_code = response_status
        log_properties.record_duration_ms()

        logger.info("Http call", properties=log_properties.model_dump())

        return response_text, response_status
    except Exception as re:
        logger.error(f"Error making {method.value} request to {path} endpoint: {str(re)}")
        raise