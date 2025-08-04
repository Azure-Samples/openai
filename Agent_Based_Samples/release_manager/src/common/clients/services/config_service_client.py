# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from http import HTTPStatus

from common.clients.http.client import HttpMethod, make_request_async
from common.contracts.configuration.config_type import ConfigType
from common.telemetry.app_logger import AppLogger


class ConfigServiceClient:
    def __init__(self, base_uri: str, logger: AppLogger):
        self.base_uri = base_uri
        self.logger = logger

    async def _fetch_config(self, path: str) -> tuple[dict | None, int]:
        """
        Internal method to fetch configuration from any config endpoint
        """
        self.logger.info(f"ConfigHub: Making GET call to: {self.base_uri}{path}")

        json_config_response, status_code = await make_request_async(
            self.base_uri, path, HttpMethod.GET, self.logger, True
        )
        try:
            if status_code != 200:
                self.logger.error(
                    f"Error fetching configuration. Response: {json_config_response}, status_code: {status_code}"
                )
                return None, status_code

            return json.loads(json_config_response), status_code

        except (KeyError, ValueError) as e:
            self.logger.error(f"Error parsing config_hub response. Response: {json_config_response}. Error: {e}")
            return None, HTTPStatus.INTERNAL_SERVER_ERROR.value

    async def get_config(self, config_type: ConfigType, config_version: str):
        path = f"/configuration-service/configs/{config_type.value}/{config_version}"
        return await self._fetch_config(path)
