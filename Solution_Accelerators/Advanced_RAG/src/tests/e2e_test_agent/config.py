#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from dotenv import load_dotenv

# load value from .debug.env file if it exists, unless deploying in a production environment
if os.getenv("ENVIRONMENT") != "PROD":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(override=True, dotenv_path=f"{current_dir}/.debug.env")

class ConfigReader():
    def read_config_value(self, key_name:str)-> str:
        return self._get_config_value(key_name)
    
    def _get_secret_from_keyvault(self, key_name:str):
        KEYVAULT_URI = os.getenv("KEYVAULT-URI", "")
        keyvault_uri_file = '/mnt/secrets-store/KEYVAULT-URI'

        if os.path.exists(keyvault_uri_file) and KEYVAULT_URI == "":
            with open(keyvault_uri_file, "r") as f:
                KEYVAULT_URI = f.read().strip()
        
        key_name = key_name.replace("_", "-")

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=KEYVAULT_URI, credential=credential)
        return client.get_secret(key_name).value

    def _get_config_value(self, key_name:str)-> str:

        value = os.getenv(key_name)

        if value is None or value == "":
            value = self._get_secret_from_keyvault(key_name)
        
        if value is None:
            raise Exception(f"Necessary value {value} couldn't be found in environment or KeyVault")
        
        return value

class DefaultConfig:
    _initialized = False

    @classmethod
    def initialize(cls):
        if not cls._initialized:
            config_reader = ConfigReader()

            try:
                cls.AZURE_OPENAI_GPT4_SERVICE = config_reader.read_config_value("AZURE-OPENAI-SERVICE-1-ENDPOINT")
                cls.AZURE_OPENAI_GPT4_API_KEY = config_reader.read_config_value("AZURE-OPENAI-SERVICE-1-KEY")
                cls.AZURE_OPENAI_SEED = int(config_reader.read_config_value("AZURE-OPENAI-SEED"))
                
                cls.SESSION_MANAGER_URI = config_reader.read_config_value("SESSION-MANAGER-URI")

                cls.AZURE_STORAGE_ACCOUNT = config_reader.read_config_value("AZURE-STORAGE-ACCOUNT")
                cls.AZURE_BLOB_CONTAINER_NAME_E2E_TEST = config_reader.read_config_value("AZURE-BLOB-CONTAINER-NAME-E2E-TEST")

                cls.CONVERSATION_DEPTH = int(config_reader.read_config_value("CONVERSATION-DEPTH"))
                cls._initialized = True
            
            except Exception as e:
                print(f"Error while loading config: {e}")
                raise e