import os
import time
from enum import Enum

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from common.telemetry.log_helper import CustomLogger


class Config(Enum):
    APPLICATION_INSIGHTS_CNX_STR = "APPLICATION-INSIGHTS-CNX-STR"
    # Azure Cosmos DB configuration
    AZURE_COSMOS_ENDPOINT = "AZURE-COSMOS-ENDPOINT"
    AZURE_COSMOS_KEY = "AZURE-COSMOS-KEY"
    AZURE_COSMOS_DB_NAME = "AZURE-COSMOS-DB-NAME"
    AZURE_COSMOS_DB_CONFIGURATION_CONTAINER_NAME = "AZURE-COSMOS-DB-CONFIGURATION-CONTAINER-NAME"
    AZURE_COSMOS_DB_ENTITIES_CONTAINER_NAME = "AZURE-COSMOS-DB-ENTITIES-CONTAINER-NAME"
    AZURE_COSMOS_DB_CHAT_SESSIONS_CONTAINER_NAME = "AZURE-COSMOS-DB-CHAT-SESSIONS-CONTAINER-NAME"
    # Azure Storage configuration
    AZURE_STORAGE_ACCOUNT = "AZURE-STORAGE-ACCOUNT"
    AZURE_STORAGE_CONTAINER = "AZURE-STORAGE-CONTAINER"
    AZURE_STORAGE_IMAGE_CONTAINER = "AZURE-STORAGE-IMAGE-CONTAINER"
    AZURE_DOCUMENT_PAGES_STORAGE_CONTAINER = "AZURE-DOCUMENT-PAGES-STORAGE-CONTAINER"
    # Azure OpenAI configuration
    AZURE_OPENAI_ENDPOINT = "AZURE-OPENAI-ENDPOINT"
    AZURE_OPENAI_KEY = "AZURE-OPENAI-KEY"
    AZURE_OPENAI_DEPLOYMENT_NAME = "AZURE-OPENAI-DEPLOYMENT-NAME"
    AZURE_OPENAI_EMBEDDINGS_ENGINE_NAME = "AZURE-OPENAI-EMBEDDINGS-ENGINE-NAME"
    # Azure Document Intelligence configuration
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = "AZURE-DOCUMENT-INTELLIGENCE-ENDPOINT"
    AZURE_DOCUMENT_INTELLIGENCE_KEY = "AZURE-DOCUMENT-INTELLIGENCE-KEY"
    AZURE_DOCUMENT_INTELLIGENCE_MODEL = "AZURE-DOCUMENT-INTELLIGENCE-MODEL"
    DEFAULT_DOCUMENT_LOADER = "DEFAULT-DOCUMENT-LOADER"
    DEFAULT_DOCUMENT_SPLITTER = "DEFAULT-DOCUMENT-SPLITTER"
    MARKDOWN_HEADER_SPLIT_CONFIG = "MARKDOWN-HEADER-SPLIT-CONFIG"
    DOCUMENT_MAX_CHUNK_SIZE = "DOCUMENT-MAX-CHUNK-SIZE"
    MARKDOWN_CONTENT_INCLUDE_IMAGE_CAPTIONS = "MARKDOWN-CONTENT-INCLUDE-IMAGE-CAPTIONS"
    # Azure Search configuration
    AZURE_SEARCH_ENDPOINT = "AZURE-SEARCH-ENDPOINT"
    AZURE_DOCUMENT_SEARCH_INDEX_NAME = "AZURE-DOCUMENT-SEARCH-INDEX-NAME"
    # Service URLs
    SEARCH_SKILL_URI = "SEARCH-SKILL-URI"
    IMAGE_DESCRIBER_SKILL_URI = "IMAGE-DESCRIBER-SKILL-URI"
    RECOMMENDER_SKILL_URI = "RECOMMENDER-SKILL-URI"
    CONFIGURATION_SERVICE_URI = "CONFIGURATION-SERVICE-URI"
    DATA_SERVICE_URI = "DATA-SERVICE-URI"
    SESSION_MANAGER_URI = "SESSION-MANAGER-URI"
    RETAIL_ORCHESTRATOR_SERVICE_URI = "RETAIL-ORCHESTRATOR-SERVICE-URI"
    RAG_ORCHESTRATOR_SERVICE_URI = "RAG-ORCHESTRATOR-SERVICE-URI"
    # Service configuration
    SERVICE_HOST = "SERVICE-HOST"
    SERVICE_PORT = "SERVICE-PORT"
    # Redis configuration
    REDIS_HOST = "REDIS-HOST"
    REDIS_PORT = "REDIS-PORT"
    REDIS_PASSWORD = "REDIS-PASSWORD"
    REDIS_TASK_QUEUE_CHANNEL = "REDIS-TASK-QUEUE-CHANNEL"
    REDIS_MESSAGE_QUEUE_CHANNEL = "REDIS-MESSAGE-QUEUE-CHANNEL"
    MULTIMODAL_BOT_REDIS_TASK_QUEUE_CHANNEL = "MULTIMODAL-BOT-REDIS-TASK-QUEUE-CHANNEL"
    MULTIMODAL_BOT_REDIS_MESSAGE_QUEUE_CHANNEL = "MULTIMODAL-BOT-REDIS-MESSAGE-QUEUE-CHANNEL"
    REDIS_DOCUMENT_PROCESSING_TASK_QUEUE_CHANNEL = "REDIS-DOCUMENT-PROCESSING-TASK-QUEUE-CHANNEL"
    DOCUMENT_PROCESSING_MAX_WORKER_THREADS = "DOCUMENT-PROCESSING-MAX-WORKER-THREADS"
    REDIS_CATALOG_PROCESSING_TASK_QUEUE_CHANNEL = "REDIS-CATALOG-PROCESSING-TASK-QUEUE-CHANNEL"
    CATALOG_PROCESSING_MAX_WORKER_THREADS = "CATALOG-PROCESSING-MAX-WORKER-THREADS"
    # Content safety service configuration
    AZURE_CONTENT_SAFETY_SERVICE = "AZURE-CONTENT-SAFETY-SERVICE"
    ORCHESTRATOR_CONCURRENCY = "ORCHESTRATOR-CONCURRENCY"
    KEYVAULT_URI = "KEYVAULT-URI"
    SPEECH_REGION = "SPEECH-REGION"
    SPEECH_KEY = "SPEECH-KEY"
    PRUNE_SEARCH_RESULTS_FROM_HISTORY_ON_PRODUCT_SELECTION = "PRUNE-SEARCH-RESULTS-FROM-HISTORY-ON-PRODUCT-SELECTION"
    CHAT_MAX_RESPONSE_TIMEOUT_IN_SECONDS = "CHAT-MAX-RESPONSE-TIMEOUT-IN-SECONDS"
    # Azure AI Project configuration
    AZURE_SUBSCRIPTION_ID = "AZURE-SUBSCRIPTION-ID"
    AZURE_RESOURCE_GROUP = "AZURE-RESOURCE-GROUP"
    AZURE_PROJECT_NAME = "AZURE-PROJECT-NAME"


class ConfigReader:
    def __init__(self, logger: CustomLogger) -> None:
        self.logger = logger

    def set_logger(self, logger: CustomLogger):
        self.logger = logger

    def read_config_value(self, key_name: Config) -> str:
        return self._get_config_value(key_name)

    def _get_secret_from_keyvault(self, key_name: Config):
        KEYVAULT_URI = os.getenv(Config.KEYVAULT_URI.value, "")
        credential = DefaultAzureCredential()

        keyvault_uri_file = "/mnt/secrets-store/KEYVAULT-URI"

        if os.path.exists(keyvault_uri_file) and KEYVAULT_URI == "":
            with open(keyvault_uri_file, "r") as f:
                KEYVAULT_URI = f.read().strip()

        key_name = key_name.value.replace("_", "-")

        client = SecretClient(vault_url=KEYVAULT_URI, credential=credential)
        return client.get_secret(key_name).value

    def _get_config_value(self, key_name: Config) -> str:

        value = os.getenv(key_name.value)

        if value is None or value == "":
            start = time.monotonic()
            value = self._get_secret_from_keyvault(key_name)
            duration_ms = (time.monotonic() - start) * 1000

            addl_dimension = {"keyvault_duration": duration_ms}

            if self.logger:
                self.logger.info(f"key name: {key_name}", properties=addl_dimension)
        if value is None:
            if self.logger:
                self.logger.error(f"Necessary value {value} couldn't be found in environment or Key Vault")
            raise Exception(f"Necessary value {value} couldn't be found in environment or Key Vault")
        return value
