# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pydantic import ValidationError

from common.contracts.configuration.service_config import ServiceSettings, GlobalServiceName, ServiceType
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureTextCompletion,
    OpenAIChatCompletion,
    OpenAITextCompletion,
    AzureTextEmbedding,
)
from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatCompletion,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def get_service(
    service_settings: ServiceSettings,
    env_file_path: str | None = None,
):
    """
    Configure the AI service for the kernel

    Args:
        kernel (Kernel): The kernel to configure
        env_file_path (str | None): The absolute or relative file path to the .env file.

    Returns: The configured AI service
    """
    if not service_settings.global_llm_service:
        service_settings.global_llm_service = GlobalServiceName.AZURE_OPENAI

    service_id = "default"
    if service_settings.service_id:
        service_id = service_settings.service_id

    # Note: Currently, only one global service is supported i.e. configure all services to use the same global service
    if service_settings.global_llm_service == GlobalServiceName.OPENAI:
        if service_settings.service_type == ServiceType.CHAT:
            completion_class = OpenAIChatCompletion
        else:
            completion_class = OpenAITextCompletion
        return completion_class(
            service_id=service_id,
            ai_model_id=service_settings.ai_model_id,
            env_file_path=env_file_path,
        )
    else:
        if service_settings.service_type == ServiceType.CHAT:
            completion_class = AzureChatCompletion
        elif service_settings.service_type == ServiceType.EMBEDDING:
            completion_class = AzureTextEmbedding
        elif service_settings.service_type == ServiceType.INFERENCE:
            return AzureAIInferenceChatCompletion(
                service_id=service_settings.service_id,
                ai_model_id=service_settings.ai_model_id,
                env_file_path=env_file_path,
            )
        return completion_class(
            service_id=service_id,
            deployment_name=service_settings.deployment_name,
            env_file_path=env_file_path,
        )
