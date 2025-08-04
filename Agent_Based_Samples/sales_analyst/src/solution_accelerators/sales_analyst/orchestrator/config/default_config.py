# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

from dotenv import load_dotenv

from common.telemetry.app_logger import AppLogger
from common.telemetry.app_tracer_provider import AppTracerProvider
from common.telemetry.log_helper import CustomLogger
from common.utilities.config_reader import Config, ConfigReader


def str_to_bool(s):
    return s.lower() == "true"


# load value from .debug.env file if it exists, unless deploying in a production environment
if os.getenv("ENVIRONMENT") != "PROD":
    load_dotenv(override=True, dotenv_path=f"{os.getcwd()}/.env")


class DefaultConfig:
    _initialized = False

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            config_reader = ConfigReader(None)

            APPLICATION_INSIGHTS_CNX_STR = config_reader.read_config_value(Config.APPLICATION_INSIGHTS_CNX_STR)
            cls.tracer_provider = AppTracerProvider(APPLICATION_INSIGHTS_CNX_STR)
            cls.logger = AppLogger(connection_string=APPLICATION_INSIGHTS_CNX_STR)
            cls.logger.set_base_properties({"ApplicationName": "ORCHESTRATOR_SERVICE"})
            config_reader.set_logger(cls.logger)

            try:
                cls.REDIS_HOST = config_reader.read_config_value(Config.REDIS_HOST)
                cls.REDIS_PORT = config_reader.read_config_value(Config.REDIS_PORT)
                cls.REDIS_PASSWORD = config_reader.read_config_value(Config.REDIS_PASSWORD)

                cls.REDIS_TASK_QUEUE_CHANNEL = config_reader.read_config_value(Config.REDIS_TASK_QUEUE_CHANNEL)
                cls.REDIS_MESSAGE_QUEUE_CHANNEL = config_reader.read_config_value(Config.REDIS_MESSAGE_QUEUE_CHANNEL)

                cls.AGENT_ORCHESTRATOR_MAX_CONCURRENCY = int(
                    config_reader.read_config_value(Config.AGENT_ORCHESTRATOR_MAX_CONCURRENCY)
                )

                cls.AZURE_AI_AGENT_ENDPOINT = config_reader.read_config_value(Config.AZURE_AI_AGENT_ENDPOINT)
                cls.AZURE_AI_DATABRICKS_CONNECTION_NAME = config_reader.read_config_value(
                    Config.AZURE_AI_DATABRICKS_CONNECTION_NAME
                )
                cls.AZURE_AI_BING_GROUNDING_CONNECTION_NAME = config_reader.read_config_value(
                    Config.AZURE_AI_BING_GROUNDING_CONNECTION_NAME
                )

                cls.SERVICE_HOST = os.getenv(Config.SERVICE_HOST.value, "0.0.0.0")
                cls.SERVICE_PORT = int(os.getenv(Config.SERVICE_PORT.value, "5102"))

                cls.STORAGE_ACCOUNT_NAME = config_reader.read_config_value(Config.STORAGE_ACCOUNT_NAME)
                cls.VISUALIZATION_DATA_CONTAINER = config_reader.read_config_value(Config.VISUALIZATION_DATA_CONTAINER)

                cls.TENANT_ID = config_reader.read_config_value(Config.TENANT_ID)
                cls.CLIENT_ID = config_reader.read_config_value(Config.CLIENT_ID)
                cls.CLIENT_SECRET = config_reader.read_config_value(Config.CLIENT_SECRET)

                cls._initialized = True

            except Exception as e:
                cls.logger.error(f"Error while loading config: {e}")
                raise e
