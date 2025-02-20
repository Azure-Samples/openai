#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import logging
from common.telemetry.app_logger import AppLogger
from common.telemetry.log_helper import CustomLogger
from dotenv import load_dotenv

from common.utilities.config_reader import Config, ConfigReader

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

# load value from .debug.env file if it exists, unless deploying in a production environment
if os.getenv("ENVIRONMENT") != "PROD":
    load_dotenv(override=True, dotenv_path=f"{os.path.dirname(__file__)}/.debug.env")

class DefaultConfig:
    _initialized = False

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            config_reader = ConfigReader(None)
            APPLICATION_INSIGHTS_CNX_STR = config_reader.read_config_value(Config.APPLICATION_INSIGHTS_CNX_STR)

            cls.custom_logger = CustomLogger(APPLICATION_INSIGHTS_CNX_STR)
            cls.logger = AppLogger(cls.custom_logger)
            cls.logger.set_base_properties({"ApplicationName": "SIM-TEST"})
            config_reader.set_logger(cls.logger)

            try:
                cls.SESSION_MANAGER_URL = config_reader.read_config_value(Config.SESSION_MANAGER_URI)
                cls._initialized = True
                cls.AZURE_OPENAI_ENDPOINT = config_reader.read_config_value(Config.AZURE_OPENAI_ENDPOINT)
                cls.AZURE_OPENAI_DEPLOYMENT_NAME = config_reader.read_config_value(Config.AZURE_OPENAI_DEPLOYMENT_NAME)
                cls.AZURE_SUBSCRIPTION_ID = config_reader.read_config_value(Config.AZURE_SUBSCRIPTION_ID)
                cls.AZURE_RESOURCE_GROUP = config_reader.read_config_value(Config.AZURE_RESOURCE_GROUP)
                cls.AZURE_PROJECT_NAME = config_reader.read_config_value(Config.AZURE_PROJECT_NAME)

            except Exception as e:
                cls.logger.error(f"Error while loading config: {e}")
                raise e