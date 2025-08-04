# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
import time
from enum import Enum

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from common.telemetry.app_logger import AppLogger


class Config(Enum):
    # Telemetry configuration
    APPLICATION_INSIGHTS_CNX_STR = "APPLICATION-INSIGHTS-CNX-STR"
    # Azure KeyVault configuration
    KEYVAULT_URI = "KEYVAULT-URI"
    # Azure Cosmos DB configuration
    AZURE_COSMOS_ENDPOINT = "AZURE-COSMOS-ENDPOINT"
    AZURE_COSMOS_KEY = "AZURE-COSMOS-KEY"
    AZURE_COSMOS_DB_NAME = "AZURE-COSMOS-DB-NAME"
    AZURE_COSMOS_DB_CONFIGURATION_CONTAINER_NAME = "AZURE-COSMOS-DB-CONFIGURATION-CONTAINER-NAME"
    # Azure Storage configuration
    AZURE_STORAGE_ACCOUNT = "AZURE-STORAGE-ACCOUNT"
    AZURE_STORAGE_CONTAINER = "AZURE-STORAGE-CONTAINER"
    AZURE_STORAGE_IMAGE_CONTAINER = "AZURE-STORAGE-IMAGE-CONTAINER"
    # Azure OpenAI configuration
    AZURE_OPENAI_ENDPOINT = "AZURE-OPENAI-ENDPOINT"
    AZURE_OPENAI_KEY = "AZURE-OPENAI-KEY"
    AZURE_OPENAI_DEPLOYMENT_NAME = "AZURE-OPENAI-DEPLOYMENT-NAME"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME = "AZURE-OPENAI-EMBEDDING-DEPLOYMENT-NAME"
    # Azure Search configuration
    AZURE_SEARCH_ENDPOINT = "AZURE-SEARCH-ENDPOINT"
    # Azure Content Understanding configuration
    AZURE_CONTENT_UNDERSTANDING_ENDPOINT = "AZURE-CONTENT-UNDERSTANDING-ENDPOINT"
    AZURE_CONTENT_UNDERSTANDING_API_KEY = "AZURE-CONTENT-UNDERSTANDING-KEY"
    # Service URLs
    CONFIGURATION_SERVICE_URI = "CONFIGURATION-SERVICE-URI"
    SESSION_MANAGER_URI = "SESSION-MANAGER-URI"
    ORCHESTRATOR_SERVICE_URI = "ORCHESTRATOR-SERVICE-URI"
    # Service configuration
    SERVICE_HOST = "SERVICE-HOST"
    SERVICE_PORT = "SERVICE-PORT"
    # Redis configuration
    REDIS_HOST = "REDIS-HOST"
    REDIS_PORT = "REDIS-PORT"
    REDIS_PASSWORD = "REDIS-PASSWORD"
    REDIS_TASK_QUEUE_CHANNEL = "REDIS-TASK-QUEUE-CHANNEL"
    REDIS_MESSAGE_QUEUE_CHANNEL = "REDIS-MESSAGE-QUEUE-CHANNEL"
    # Content safety service configuration
    AZURE_CONTENT_SAFETY_SERVICE = "AZURE-CONTENT-SAFETY-SERVICE"
    # Azure AI Project configuration
    AZURE_SUBSCRIPTION_ID = "AZURE-SUBSCRIPTION-ID"
    AZURE_RESOURCE_GROUP = "AZURE-RESOURCE-GROUP"
    AZURE_PROJECT_NAME = "AZURE-PROJECT-NAME"
    # Azure AI Foundry Configuration
    AZURE_AI_AGENT_PROJECT_CONNECTION_STRING = "AZURE-AI-AGENT-PROJECT-CONNECTION-STRING"
    AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME = "AZURE-AI-AGENT-MODEL-DEPLOYMENT-NAME"
    # Azure AI ML configuration
    AZURE_WORKSPACE_NAME = "AZURE-WORKSPACE-NAME"

    AZURE_AI_AGENT_ENDPOINT = "AZURE-AI-AGENT-ENDPOINT"
    AZURE_AI_DATABRICKS_CONNECTION_NAME = "AZURE-AI-DATABRICKS-CONNECTION-NAME"
    AZURE_AI_BING_GROUNDING_CONNECTION_NAME = "AZURE-AI-BING-GROUNDING-CONNECTION-NAME"

    # Service-specific configuration
    CHAT_MAX_RESPONSE_TIMEOUT_IN_SECONDS = "CHAT-MAX-RESPONSE-TIMEOUT-IN-SECONDS"
    AGENT_ORCHESTRATOR_MAX_CONCURRENCY = "AGENT-ORCHESTRATOR-MAX-CONCURRENCY"
    STORAGE_ACCOUNT_NAME = "STORAGE-ACCOUNT-NAME"
    VISUALIZATION_DATA_CONTAINER = "VISUALIZATION-DATA-CONTAINER"

    # JIRA Settings
    JIRA_SERVER_ENDPOINT = "JIRA-SERVER-ENDPOINT"
    JIRA_SERVER_USERNAME = "JIRA-SERVER-USERNAME"
    JIRA_SERVER_PASSWORD = "JIRA-SERVER-PASSWORD"

    # DevOps Settings
    DEVOPS_DATABASE_SERVER_ENDPOINT = "DEVOPS-DATABASE-SERVER-ENDPOINT"
    DEVOPS_DATABASE_SERVER_USERNAME = "DEVOPS-DATABASE-SERVER-USERNAME"
    DEVOPS_DATABASE_SERVER_PASSWORD = "DEVOPS-DATABASE-SERVER-PASSWORD"
    DEVOPS_DATABASE_NAME = "DEVOPS-DATABASE-NAME"
    DEVOPS_DATABASE_TABLE_NAME = "DEVOPS-DATABASE-TABLE-NAME"

    # Speech configuration
    SPEECH_KEY = "SPEECH-KEY"
    SPEECH_REGION = "SPEECH-REGION"

    TENANT_ID = "TENANT-ID"
    CLIENT_ID = "CLIENT-ID"
    CLIENT_SECRET = "CLIENT-SECRET"


class ConfigReader:
    def __init__(self, logger: AppLogger) -> None:
        self.logger = logger

    def set_logger(self, logger: AppLogger):
        self.logger = logger

    def read_config_value(self, key_name: Config) -> str:
        return self._get_config_value(key_name)

    def _get_secret_from_keyvault(self, key_name: Config):
        KEYVAULT_URI = os.getenv(Config.KEYVAULT_URI.value, "") or os.getenv("KEYVAULT_URI", "")
        credential = DefaultAzureCredential()

        keyvault_uri_file = "/mnt/secrets-store/KEYVAULT-URI"

        if os.path.exists(keyvault_uri_file) and KEYVAULT_URI == "":
            with open(keyvault_uri_file, "r") as f:
                KEYVAULT_URI = f.read().strip()

        key_name = key_name.value.replace("_", "-")

        client = SecretClient(vault_url=KEYVAULT_URI, credential=credential)
        return client.get_secret(key_name).value

    def _get_config_value(self, key_name: Config) -> str:
        key_name_updated = key_name.value.replace("-", "_")
        value = os.getenv(key_name.value) or os.getenv(key_name_updated)

        if value is None or value == "":
            start = time.monotonic()
            value = self._get_secret_from_keyvault(key_name)
            duration_ms = (time.monotonic() - start) * 1000

            addl_dimension = {"keyvault_duration": duration_ms}

            if self.logger:
                self.logger.info(f"key name: {key_name}", properties=addl_dimension)
        if value is None:
            if self.logger:
                self.logger.error(f"Necessary value {key_name} couldn't be found in environment or Key Vault")
            raise Exception(f"Necessary value {key_name} couldn't be found in environment or Key Vault")
        return value
