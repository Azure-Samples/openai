#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

from dotenv import load_dotenv

from common.telemetry.app_logger import AppLogger
from common.telemetry.log_helper import CustomLogger
from common.utilities.config_reader import Config, ConfigReader

# load value from .debug.env file if it exists, unless deploying in a production environment
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
            logger.set_base_properties({"ApplicationName": "RAG_EVAL"})
            config_reader.set_logger(logger)

            try:
                cls.CONFIGURATION_SERVICE_URL = config_reader.read_config_value(Config.CONFIGURATION_SERVICE_URL)
                cls.AZURE_OPENAI_ENDPOINT = config_reader.read_config_value(Config.AZURE_OPENAI_ENDPOINT)
                cls._initialized = True

            except Exception as e:
                logger.error(f"Error while loading config: {e}")
                raise e