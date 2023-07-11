#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from common.logging.log_helper import CustomLogger
from datetime import datetime
from dotenv import load_dotenv

# load value from .env file if it exists followed by environment variables
if os.getenv("ENVIRONMENT") != "PROD":
    load_dotenv(override=True, dotenv_path=f"{os.getcwd()}/data/.env")

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
            cls.logger.set_conversation_and_dialog_ids("DATASERVICE_APP", "NONE")
            config_reader.set_logger(cls.logger)

            try:
                cls.COSMOS_DB_ENDPOINT = config_reader.read_config_value("AZURE-COSMOS-ENDPOINT")
                cls.COSMOS_DB_NAME = config_reader.read_config_value("AZURE-COSMOS-DB-NAME")
                cls.COSMOS_DB_KEY = config_reader.read_config_value("AZURE-COSMOS-KEY")
                cls.COSMOS_DB_ENTITIES_CONTAINER_NAME = config_reader.read_config_value("AZURE-COSMOS-DB-ENTITIES-CONTAINER-NAME")
                cls.COSMOS_DB_PERMISSIONS_CONTAINER_NAME = config_reader.read_config_value("AZURE-COSMOS-DB-PERMISSIONS-CONTAINER-NAME")
                cls.COSMOS_DB_CHAT_SESSIONS_CONTAINER_NAME = config_reader.read_config_value("AZURE-COSMOS-DB-CHAT-SESSIONS-CONTAINER-NAME")

                cls.DATA_SERVICE_HOST = os.getenv("DATA-SERVICE-HOST", "") if os.getenv("DATA-SERVICE-HOST") != "" else ""
                cls.DATA_SERVICE_PORT = os.getenv("DATA-SERVICE-PORT", "") if os.getenv("DATA-SERVICE-PORT") != "" else ""

                cls._initialized = True
                
            except Exception as e:
                cls.logger.error(f"Error while loading config: {e}")
                raise e