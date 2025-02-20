#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import time
from common.telemetry.app_logger import AppLogger
from common.telemetry.log_helper import CustomLogger
from common.utilities.config_reader import ConfigReader, Config
from dotenv import load_dotenv

# load value from .debug.env file if it exists followed by environment variables
if os.getenv("ENVIRONMENT") != "PROD":
    load_dotenv(override=True, dotenv_path=f"{os.getcwd()}/.debug.env")

class DefaultConfig:
    _initialized = False

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            config_reader = ConfigReader(None)

            APPLICATION_INSIGHTS_CNX_STR = config_reader.read_config_value(Config.APPLICATION_INSIGHTS_CNX_STR)

            cls.custom_logger = CustomLogger(APPLICATION_INSIGHTS_CNX_STR)
            logger = AppLogger(cls.custom_logger)
            logger.set_base_properties({"ApplicationName": "DATA_SERVICE"})
            config_reader.set_logger(logger)

            try:
                cls.SERVICE_HOST = os.getenv(Config.SERVICE_HOST.value, "0.0.0.0")
                cls.SERVICE_PORT = os.getenv(Config.SERVICE_PORT.value, "5001")

                cls.COSMOS_DB_ENDPOINT = config_reader.read_config_value(Config.AZURE_COSMOS_ENDPOINT)
                cls.COSMOS_DB_NAME = config_reader.read_config_value(Config.AZURE_COSMOS_DB_NAME)
                cls.COSMOS_DB_KEY = config_reader.read_config_value(Config.AZURE_COSMOS_KEY)
                cls.COSMOS_DB_ENTITIES_CONTAINER_NAME = config_reader.read_config_value(Config.AZURE_COSMOS_DB_ENTITIES_CONTAINER_NAME)
                cls.COSMOS_DB_CHAT_SESSIONS_CONTAINER_NAME = config_reader.read_config_value(Config.AZURE_COSMOS_DB_CHAT_SESSIONS_CONTAINER_NAME)
                
                cls._initialized = True
                
            except Exception as e:
                logger.error(f"Error while loading config: {e}")
                raise e