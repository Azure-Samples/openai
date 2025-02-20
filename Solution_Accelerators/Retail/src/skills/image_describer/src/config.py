import os
from dotenv import load_dotenv

from common.telemetry.app_logger import AppLogger
from common.telemetry.log_helper import CustomLogger
from common.utilities.config_reader import ConfigReader, Config

# load value from .env file if it exists, unless deploying in a production environment
if os.getenv("ENVIRONMENT") != "PROD":
    dotenv_path = os.path.join(os.path.dirname(os.getcwd()), '.debug.env')
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
            logger.set_base_properties({"ApplicationName": "IMAGE_DESCRIBER_SKILL"})
            config_reader.set_logger(logger)

            try:
                cls.SERVICE_HOST = os.getenv(Config.SERVICE_HOST.value, "0.0.0.0")
                cls.SERVICE_PORT = os.getenv(Config.SERVICE_PORT.value, "6004")
                cls.IMAGE_ANALYSIS_DEFAULT_ANALYZER_SERVICE = os.getenv("IMAGE_ANALYSIS_DEFAULT_ANALYZER_SERVICE", "openai")

                cls.AZURE_OPENAI_ENDPOINT = config_reader.read_config_value(Config.AZURE_OPENAI_ENDPOINT)
                
                cls.AZURE_STORAGE_ACCOUNT_NAME = config_reader.read_config_value(Config.AZURE_STORAGE_ACCOUNT)
                cls.AZURE_STORAGE_IMAGE_CONTAINER = config_reader.read_config_value(Config.AZURE_STORAGE_IMAGE_CONTAINER)
                cls._initialized = True

            except Exception as e:
                logger.error(f"Error while loading config: {e}")
                raise e