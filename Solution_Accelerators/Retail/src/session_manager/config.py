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


def str_to_bool(s):
    return s.lower() == "true"


class DefaultConfig:
    _initialized = False

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            config_reader = ConfigReader(None)

            APPLICATION_INSIGHTS_CNX_STR = config_reader.read_config_value(Config.APPLICATION_INSIGHTS_CNX_STR)

            cls.custom_logger = CustomLogger(APPLICATION_INSIGHTS_CNX_STR)
            logger = AppLogger(cls.custom_logger)
            config_reader.set_logger(logger)

            try:
                cls.SESSION_MANAGER_URI = config_reader.read_config_value(Config.SESSION_MANAGER_URI)

                cls.SERVICE_HOST = os.getenv(Config.SERVICE_HOST.value, "0.0.0.0")
                cls.SERVICE_PORT = int(os.getenv(Config.SERVICE_PORT.value, "5000"))

                cls.AZURE_STORAGE_CONTAINER = config_reader.read_config_value(Config.AZURE_STORAGE_CONTAINER)
                cls.AZURE_STORAGE_IMAGE_CONTAINER = config_reader.read_config_value(
                    Config.AZURE_STORAGE_IMAGE_CONTAINER
                )
                cls.AZURE_STORAGE_ACCOUNT = config_reader.read_config_value(Config.AZURE_STORAGE_ACCOUNT)

                cls.AZURE_CONTENT_SAFETY_SERVICE = config_reader.read_config_value(Config.AZURE_CONTENT_SAFETY_SERVICE)

                cls.DATA_SERVICE_URI = config_reader.read_config_value(Config.DATA_SERVICE_URI)

                cls.RETAIL_ORCHESTRATOR_SERVICE_URI = config_reader.read_config_value(
                    Config.RETAIL_ORCHESTRATOR_SERVICE_URI
                )
                cls.RAG_ORCHESTRATOR_SERVICE_URI = config_reader.read_config_value(Config.RAG_ORCHESTRATOR_SERVICE_URI)

                cls.CONFIGURATION_SERVICE_URI = config_reader.read_config_value(Config.CONFIGURATION_SERVICE_URI)

                cls.PRUNE_SEARCH_RESULTS_FROM_HISTORY_ON_PRODUCT_SELECTION = config_reader.read_config_value(
                    Config.PRUNE_SEARCH_RESULTS_FROM_HISTORY_ON_PRODUCT_SELECTION
                )

                cls.SPEECH_REGION = None
                cls.SPEECH_KEY = None

                try:
                    cls.SPEECH_REGION = config_reader.read_config_value(Config.SPEECH_REGION)
                    cls.SPEECH_KEY = config_reader.read_config_value(Config.SPEECH_KEY)
                except Exception as e:
                    logger.error(f"Error while loading speech region and key: {e}")
                    logger.info("Speech region and key are not set. Speech features will be disabled.")

                cls.REDIS_HOST = config_reader.read_config_value(Config.REDIS_HOST)
                cls.REDIS_PORT = int(config_reader.read_config_value(Config.REDIS_PORT))
                cls.REDIS_PASSWORD = config_reader.read_config_value(Config.REDIS_PASSWORD)

                cls.SESSION_MANAGER_CHAT_REQUEST_TASK_QUEUE_CHANNEL = config_reader.read_config_value(
                    Config.REDIS_TASK_QUEUE_CHANNEL
                )
                cls.SESSION_MANAGER_CHAT_RESPONSE_MESSAGE_QUEUE_CHANNEL = config_reader.read_config_value(
                    Config.REDIS_MESSAGE_QUEUE_CHANNEL
                )

                cls.SESSION_MANAGER_CHAT_REQUEST_TASK_QUEUE_CHANNEL_RETAIL = config_reader.read_config_value(
                    Config.MULTIMODAL_BOT_REDIS_TASK_QUEUE_CHANNEL
                )
                cls.SESSION_MANAGER_CHAT_RESPONSE_MESSAGE_QUEUE_CHANNEL_RETAIL = config_reader.read_config_value(
                    Config.MULTIMODAL_BOT_REDIS_MESSAGE_QUEUE_CHANNEL
                )

                cls.CHAT_MAX_RESPONSE_TIMEOUT_IN_SECONDS = int(
                    config_reader.read_config_value(Config.CHAT_MAX_RESPONSE_TIMEOUT_IN_SECONDS)
                )

                cls._initialized = True

            except Exception as e:
                logger.error(f"Error while loading config: {e}")
                raise e
