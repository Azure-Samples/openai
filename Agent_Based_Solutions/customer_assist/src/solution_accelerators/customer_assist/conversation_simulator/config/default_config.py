# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

from dotenv import load_dotenv

from common.telemetry.app_logger import AppLogger
from common.telemetry.log_helper import CustomLogger
from common.utilities.config_reader import Config, ConfigReader

# load value from .env file if it exists, unless deploying in a production environment
if os.getenv("ENVIRONMENT") != "PROD":
    load_dotenv(override=True, dotenv_path=f"{os.getcwd()}/.env")


class DefaultConfig:
    _initialized = False

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            config_reader = ConfigReader(None)

            APPLICATION_INSIGHTS_CNX_STR = config_reader.read_config_value(
                Config.APPLICATION_INSIGHTS_CNX_STR
            )

            cls.custom_logger = CustomLogger(APPLICATION_INSIGHTS_CNX_STR)
            logger = AppLogger(connection_string=APPLICATION_INSIGHTS_CNX_STR)
            logger.set_base_properties({"ApplicationName": "Conversation_Simulator"})
            config_reader.set_logger(logger)

            try:
                cls.SERVICE_HOST = os.getenv(Config.SERVICE_HOST.value, "0.0.0.0")
                cls.SERVICE_PORT = int(os.getenv(Config.SERVICE_PORT.value, "6001"))

                cls._initialized = True

            except Exception as e:
                logger.error(f"Error while loading config: {e}")
                raise e
