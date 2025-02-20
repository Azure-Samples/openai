import os
import time
from dotenv import load_dotenv

from common.telemetry.app_logger import AppLogger
from common.telemetry.log_helper import CustomLogger
from common.utilities.config_reader import ConfigReader, Config

load_dotenv()

if os.getenv("ENVIRONMENT") != "PROD":
    dotenv_path = os.path.join(os.getcwd(), '.debug.env')
    if os.path.exists(dotenv_path):
        load_dotenv(override=True, dotenv_path=dotenv_path)    
    else:        
        print(f"Warning: .env file not found at {dotenv_path}")

class DefaultConfig:
    _initialized = False

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            config_reader = ConfigReader(None)

            APPLICATION_INSIGHTS_CNX_STR = config_reader.read_config_value(Config.APPLICATION_INSIGHTS_CNX_STR)

            cls.custom_logger = CustomLogger(APPLICATION_INSIGHTS_CNX_STR)
            logger = AppLogger(cls.custom_logger)
            logger.set_base_properties({"ApplicationName": "DOCUMENT_INDEXER_SKILL"})
            config_reader.set_logger(logger)

            try:
                # App Settings
                cls.SERVICE_HOST = os.getenv(Config.SERVICE_HOST.value, "0.0.0.0")
                cls.SERVICE_PORT = os.getenv(Config.SERVICE_PORT.value, "6001")

                # OpenAI Settings
                cls.AZURE_OPENAI_ENDPOINT = config_reader.read_config_value(Config.AZURE_OPENAI_ENDPOINT)
                cls.AZURE_OPENAI_EMBEDDINGS_ENGINE_NAME = config_reader.read_config_value(Config.AZURE_OPENAI_EMBEDDINGS_ENGINE_NAME)

                # Azure Document Intelligence Settings
                cls.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = config_reader.read_config_value(Config.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT)
                cls.AZURE_DOCUMENT_INTELLIGENCE_KEY = config_reader.read_config_value(Config.AZURE_DOCUMENT_INTELLIGENCE_KEY)
                cls.AZURE_DOCUMENT_INTELLIGENCE_MODEL = config_reader.read_config_value(Config.AZURE_DOCUMENT_INTELLIGENCE_MODEL)
                cls.DEFAULT_DOCUMENT_LOADER = config_reader.read_config_value(Config.DEFAULT_DOCUMENT_LOADER)
                cls.DEFAULT_DOCUMENT_SPLITTER = config_reader.read_config_value(Config.DEFAULT_DOCUMENT_SPLITTER)
                cls.MARKDOWN_HEADER_SPLIT_CONFIG = config_reader.read_config_value(Config.MARKDOWN_HEADER_SPLIT_CONFIG)
                cls.DOCUMENT_MAX_CHUNK_SIZE = int(config_reader.read_config_value(Config.DOCUMENT_MAX_CHUNK_SIZE))
                cls.MARKDOWN_CONTENT_INCLUDE_IMAGE_CAPTIONS = config_reader.read_config_value(Config.MARKDOWN_CONTENT_INCLUDE_IMAGE_CAPTIONS).lower() == "true"

                # Azure AI Search Settings
                cls.AZURE_SEARCH_ENDPOINT = config_reader.read_config_value(Config.AZURE_SEARCH_ENDPOINT)
                cls.AZURE_DOCUMENT_SEARCH_INDEX_NAME = config_reader.read_config_value(Config.AZURE_DOCUMENT_SEARCH_INDEX_NAME)

                # Azure Storage Settings
                cls.AZURE_STORAGE_ACCOUNT_NAME = config_reader.read_config_value(Config.AZURE_STORAGE_ACCOUNT)

                # Redis settings
                cls.REDIS_HOST = config_reader.read_config_value(Config.REDIS_HOST)
                cls.REDIS_PORT = int(config_reader.read_config_value(Config.REDIS_PORT))
                cls.REDIS_PASSWORD = config_reader.read_config_value(Config.REDIS_PASSWORD)
                cls.DOCUMENT_PROCESSING_TASK_QUEUE_CHANNEL = config_reader.read_config_value(Config.REDIS_DOCUMENT_PROCESSING_TASK_QUEUE_CHANNEL)
                cls.DOCUMENT_PROCESSING_MAX_WORKER_THREADS = int(config_reader.read_config_value(Config.DOCUMENT_PROCESSING_MAX_WORKER_THREADS))
                cls.CATALOG_PROCESSING_TASK_QUEUE_CHANNEL = config_reader.read_config_value(Config.REDIS_CATALOG_PROCESSING_TASK_QUEUE_CHANNEL)
                cls.CATALOG_PROCESSING_MAX_WORKER_THREADS = int(config_reader.read_config_value(Config.CATALOG_PROCESSING_MAX_WORKER_THREADS))

                cls._initialized = True

            except Exception as e:
                logger.error(f"Error while loading config: {e}")
                raise e