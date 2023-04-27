#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from dotenv import load_dotenv
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

load_dotenv()

def get_secret_from_keyvault( key_name:str):
    KEYVAULT_NAME = os.getenv("KEYVAULTNAME", "")
    KVUri = f"https://{KEYVAULT_NAME}.vault.azure.net/"
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KVUri, credential=credential)
    return client.get_secret(key_name).value
     
def get_config_value(key_name:str):
    value = os.getenv(key_name, None)
    if value is None:
        value = get_secret_from_keyvault(key_name)
    return value

class DefaultConfig:
    def __init__(self) -> None:
        pass

    OPENAI_RESOURCE_KEY = get_config_value("OPENAIRESOURCEKEY")
    OPENAI_RESOURCE_NAME = get_config_value("OPENAIRESOURCENAME")
    OPENAI_CHATGPT_DEPLOYMENT_NAME = get_config_value("OPENAICHATGPTDEPLOYMENTNAME")
    OPENAI_GPT_DEPLOYMENT_NAME = get_config_value("OPENAIGPTDEPLOYMENTNAME")
    OPENAI_API_VERSION = get_config_value("OPENAIAPIVERSION")

    COSMOS_DB_ENDPOINT = get_config_value("COSMOSENDPOINT")
    COSMOS_DB_NAME = get_config_value("COSMOSDBNAME")
    COSMOS_DB_KEY = get_config_value("COSMOSKEY")
    COSMOS_DB_USER_PROFILE_CONTAINER_NAME = get_config_value("COSMOSDBUSERPROFILECONTAINERNAME")
    COSMOS_DB_FAQ_CONTAINER_NAME = get_config_value("COSMOSDBFAQCONTAINERNAME")

    PORT = os.getenv("PORT", "80")
