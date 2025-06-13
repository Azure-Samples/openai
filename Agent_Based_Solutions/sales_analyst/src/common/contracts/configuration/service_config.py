# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum
from common.contracts.configuration.create_config import ConfigType
from pydantic import BaseModel
from typing import Optional, Union
from common.contracts.configuration.config_base import ConfigBase


class GlobalServiceName(str, Enum):
    OPENAI = "OpenAI"
    AZURE_OPENAI = "AzureOpenAI"


class ServiceType(str, Enum):
    CHAT = "Chat"
    EMBEDDING = "Embedding"
    INFERENCE = "Inference"


class ServiceSettings(BaseModel):
    global_llm_service: GlobalServiceName = GlobalServiceName.AZURE_OPENAI
    use_chat: bool = True
    service_id: str
    api_version: Optional[str] = None
    service_type: ServiceType = ServiceType.CHAT


class AzureOpenAIServiceSettings(ServiceSettings):
    deployment_name: str


class OpenAIServiceSettings(ServiceSettings):
    ai_model_id: str


class AzureAIInferenceServiceSettings(ServiceSettings):
    ai_model_id: str
    service_type: ServiceType = ServiceType.INFERENCE


ServiceSettingsUnion = Union[AzureOpenAIServiceSettings, OpenAIServiceSettings, AzureAIInferenceServiceSettings]


class ServiceConfig(ConfigBase):
    config_type: str = ConfigType.SERVICE.value
    config_body: ServiceSettingsUnion
