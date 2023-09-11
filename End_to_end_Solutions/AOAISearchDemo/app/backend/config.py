#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from datetime import datetime

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from common.logging.log_helper import CustomLogger
from dotenv import load_dotenv

# load value from .env file if it exists, unless deploying in a production environment
if os.getenv("ENVIRONMENT") != "PROD":
    load_dotenv(override=True, dotenv_path=f"{os.getcwd()}/backend/.env")

class Config_Reader():
    def __init__(self, logger: CustomLogger) -> None:
        self.logger = logger
    
    def set_logger(self, logger: CustomLogger):
        self.logger = logger

    def read_config_value(self, key_name:str)-> str:
        return self._get_config_value(key_name)
    
    def _get_secret_from_keyvault(self, key_name:str):
        KEYVAULT_URI = os.getenv("KEYVAULT_URI", "")
        credential = DefaultAzureCredential()
        
        key_name = key_name.replace("_", "-")

        client = SecretClient(vault_url=KEYVAULT_URI, credential=credential)
        return client.get_secret(key_name).value

    def _get_config_value(self, key_name:str)-> str:

        value = os.getenv(key_name, None)
        
        if value is None or value == "":
            start = datetime.now()
            value = self._get_secret_from_keyvault(key_name)
            end = datetime.now()
            duration = (end - start).microseconds/1000
            addl_dimension = {"keyvault_duration": duration}
            
            if self.logger:
                add_props = self.logger.get_updated_properties(addl_dimension)
                self.logger.info(f"key name: {key_name}, keyvault_duration: {duration}", extra=add_props)
        if value is None:
            if self.logger:
                self.logger.error(f"Necessary value {value} couldn't be found in environment or Key Vault")
            raise Exception(f"Necessary value {value} couldn't be found in environment or Key Vault")
        return value

class DefaultConfig:
    _initialized = False

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            config_reader = Config_Reader(None)

            APPLICATION_INSIGHTS_CNX_STR = config_reader.read_config_value("APPLICATION-INSIGHTS-CNX-STR")

            cls.logger = CustomLogger(APPLICATION_INSIGHTS_CNX_STR)
            cls.logger.set_conversation_and_dialog_ids("BACKEND_APP", "NONE")
            config_reader.set_logger(cls.logger)

            try:
                cls.AZURE_OPENAI_GPT4_SERVICE = config_reader.read_config_value("AZURE-OPENAI-GPT4-SERVICE")
                cls.AZURE_OPENAI_GPT4_API_KEY = config_reader.read_config_value("AZURE-OPENAI-GPT4-API-KEY")

                cls.AZURE_OPENAI_CLASSIFIER_SERVICE = config_reader.read_config_value("AZURE-OPENAI-CLASSIFIER-SERVICE")
                cls.AZURE_OPENAI_CLASSIFIER_API_KEY = config_reader.read_config_value("AZURE-OPENAI-CLASSIFIER-API-KEY")

                cls.AZURE_OPENAI_EMBEDDINGS_SERVICE = config_reader.read_config_value("AZURE-OPENAI-EMBEDDINGS-SERVICE")
                cls.AZURE_OPENAI_EMBEDDINGS_API_KEY = config_reader.read_config_value("AZURE-OPENAI-EMBEDDINGS-API-KEY")

                cls.AZURE_SEARCH_SERVICE = config_reader.read_config_value("AZURE-SEARCH-SERVICE")
                cls.AZURE_SEARCH_INDEX = config_reader.read_config_value("AZURE-SEARCH-INDEX")
                cls.AZURE_SEARCH_KEY = config_reader.read_config_value("AZURE-SEARCH-KEY")
                cls.KB_FIELDS_CONTENT = config_reader.read_config_value("KB-FIELDS-CONTENT")
                cls.KB_FIELDS_CATEGORY = config_reader.read_config_value("KB-FIELDS-CATEGORY")
                cls.KB_FIELDS_SOURCEPAGE = config_reader.read_config_value("KB-FIELDS-SOURCEPAGE")
                cls.SEARCH_SKIP_VECTORIZATION = config_reader.read_config_value("SEARCH-SKIP-VECTORIZATION")

                cls.AZURE_STORAGE_ACCOUNT = config_reader.read_config_value("AZURE-STORAGE-ACCOUNT")
                cls.AZURE_STORAGE_CONTAINER = config_reader.read_config_value("AZURE-STORAGE-CONTAINER")
                cls.AZURE_BLOB_CONNECTION_STRING = config_reader.read_config_value("AZURE-BLOB-CONNECTION-STRING")

                cls.DATA_SERVICE_URI = config_reader.read_config_value("DATA-SERVICE-URI")

                cls.SQL_CONNECTION_STRING = config_reader.read_config_value("SQL-CONNECTION-STRING")

                cls.RATIO_OF_INDEX_TO_HISTORY = int(os.getenv("RATIO_OF_INDEX_TO_HISTORY", 5)) if os.getenv("RATIO_OF_INDEX_TO_HISTORY") != "" else 5
                cls.SEARCH_THRESHOLD_PERCENTAGE = int(os.getenv("SEARCH_THRESHOLD_PERCENTAGE", 50)) if os.getenv("SEARCH_THRESHOLD_PERCENTAGE") != "" else 50
                cls.logger.info(f"SEARCH_THRESHOLD_PERCENTAGE: {cls.SEARCH_THRESHOLD_PERCENTAGE}")

                cls._initialized = True

            except Exception as e:
                cls.logger.error(f"Error while loading config: {e}")
                raise e