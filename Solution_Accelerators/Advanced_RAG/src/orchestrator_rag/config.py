#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from common.telemetry.app_logger import AppLogger
from common.telemetry.log_helper import CustomLogger
from common.utilities.config_reader import ConfigReader, Config
from dotenv import load_dotenv

def str_to_bool(s):
    return s.lower() == 'true'

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
            logger.set_base_properties({"ApplicationName": "ORCHESTRATOR_SERVICE"})
            config_reader.set_logger(logger)

            try:
                cls.AZURE_OPENAI_GPT_SERVICE_REPHRASER = config_reader.read_config_value(Config.AZURE_OPENAI_ENDPOINT)

                cls.AZURE_OPENAI_GPT_SERVICE_FINAL_ANSWER_GENERATOR = config_reader.read_config_value(Config.AZURE_OPENAI_ENDPOINT)

                cls.SEARCH_SKILL_URL = config_reader.read_config_value(Config.SEARCH_SKILL_URI)
                cls.CONFIGURATION_SERVICE_URL = config_reader.read_config_value(Config.CONFIGURATION_SERVICE_URI)

                cls.REDIS_HOST = config_reader.read_config_value(Config.REDIS_HOST)
                cls.REDIS_PORT = config_reader.read_config_value(Config.REDIS_PORT)
                cls.REDIS_PASSWORD = config_reader.read_config_value(Config.REDIS_PASSWORD)

                cls.REDIS_TASK_QUEUE_CHANNEL = config_reader.read_config_value(Config.REDIS_TASK_QUEUE_CHANNEL)
                cls.REDIS_MESSAGE_QUEUE_CHANNEL = config_reader.read_config_value(Config.REDIS_MESSAGE_QUEUE_CHANNEL)

                cls.ORCHESTRATOR_CONCURRENCY = int(config_reader.read_config_value(Config.ORCHESTRATOR_CONCURRENCY))

                cls.SERVICE_HOST = os.getenv(Config.SERVICE_HOST.value, "0.0.0.0")
                cls.SERVICE_PORT = os.getenv(Config.SERVICE_PORT.value, "5002")

                cls._initialized = True

            except Exception as e:
                logger.error(f"Error while loading config: {e}")
                raise e