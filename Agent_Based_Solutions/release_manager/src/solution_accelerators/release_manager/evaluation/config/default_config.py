# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os

from dotenv import load_dotenv

from common.telemetry.app_logger import AppLogger
from common.telemetry.app_tracer_provider import AppTracerProvider
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

            APPLICATION_INSIGHTS_CNX_STR = config_reader.read_config_value(Config.APPLICATION_INSIGHTS_CNX_STR)

            cls.tracer_provider = AppTracerProvider(APPLICATION_INSIGHTS_CNX_STR)
            cls.logger = AppLogger(APPLICATION_INSIGHTS_CNX_STR)
            config_reader.set_logger(cls.logger)

            try:
                cls.SESSION_MANAGER_URI = config_reader.read_config_value(Config.SESSION_MANAGER_URI)

                cls.AZURE_OPENAI_ENDPOINT = config_reader.read_config_value(Config.AZURE_OPENAI_ENDPOINT)
                cls.AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME = config_reader.read_config_value(Config.AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME)

                cls.AZURE_AI_AGENT_PROJECT_CONNECTION_STRING = config_reader.read_config_value(Config.AZURE_AI_AGENT_PROJECT_CONNECTION_STRING)
                cls.AZURE_SUBSCRIPTION_ID = config_reader.read_config_value(Config.AZURE_SUBSCRIPTION_ID)
                cls.AZURE_RESOURCE_GROUP = config_reader.read_config_value(Config.AZURE_RESOURCE_GROUP)
                cls.AZURE_WORKSPACE_NAME = config_reader.read_config_value(Config.AZURE_WORKSPACE_NAME)

                cls.JIRA_SERVER_ENDPOINT = config_reader.read_config_value(Config.JIRA_SERVER_ENDPOINT)
                cls.JIRA_SERVER_USERNAME = config_reader.read_config_value(Config.JIRA_SERVER_USERNAME)
                cls.JIRA_SERVER_PASSWORD = config_reader.read_config_value(Config.JIRA_SERVER_PASSWORD)

                cls.DEVOPS_DATABASE_SERVER_ENDPOINT = config_reader.read_config_value(Config.DEVOPS_DATABASE_SERVER_ENDPOINT)
                cls.DEVOPS_DATABASE_SERVER_USERNAME = config_reader.read_config_value(Config.DEVOPS_DATABASE_SERVER_USERNAME)
                cls.DEVOPS_DATABASE_SERVER_PASSWORD = config_reader.read_config_value(Config.DEVOPS_DATABASE_SERVER_PASSWORD)
                cls.DEVOPS_DATABASE_NAME = config_reader.read_config_value(Config.DEVOPS_DATABASE_NAME)
                cls.DEVOPS_DATABASE_TABLE_NAME = config_reader.read_config_value(Config.DEVOPS_DATABASE_TABLE_NAME)

                cls._initialized = True

            except Exception as e:
                cls.logger.error(f"Error while loading config: {e}")
                raise e