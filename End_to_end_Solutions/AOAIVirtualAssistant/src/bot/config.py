#!/usr/bin/env python3
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from dotenv import load_dotenv
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


load_dotenv()


class DefaultConfig:
    PORT = os.environ.get("PORT", "3978")
    ORCHESTRATOR_BASE_URL = os.environ.get("ORCHESTRATOR_BASE_URL", "")
    ORCHESTRATOR_QUERY_PATH = os.environ.get("CHAT_QUERY_PATH", "/query")
    ORCHESTRATOR_CLEAR_CONVERSATION_PATH = os.environ.get(
        "CLEAR_CONVERSATION_PATH", "/clearConversations")
    APP_ID = os.environ.get("MicrosoftAppId", None)
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", None)

    if APP_ID is None:
        KEYVAULT_NAME = os.getenv("KEYVAULTNAME", "")
        KVUri = f"https://{KEYVAULT_NAME}.vault.azure.net/"
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=KVUri, credential=credential)
        APP_ID = client.get_secret("MicrosoftAppId").value
        APP_PASSWORD = client.get_secret("MicrosoftAppId").value

    if APP_PASSWORD is None:
        KEYVAULT_NAME = os.getenv("KEYVAULTNAME", "")
        KVUri = f"https://{KEYVAULT_NAME}.vault.azure.net/"
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=KVUri, credential=credential)
        APP_PASSWORD = client.get_secret("MicrosoftAppId").value
