# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Literal, Optional, Union

from pydantic import BaseModel, Field
from semantic_kernel.connectors.ai import PromptExecutionSettings

from common.contracts.configuration.config_base import ConfigBase
from common.contracts.configuration.config_type import ConfigType


class SearchToolConfig(BaseModel):
    index_name: str
    # Placeholder for future Azure AI SDK updates


class BaseAgentConfig(BaseModel):
    agent_name: str


# AIFoundryAgentConfig - for Azure AI Foundry agents
class AIFoundryAgentConfig(BaseModel):
    """
    AIFoundryAgentConfig is a configuration model for an AI Foundry Agent.
    Attributes:
        model (str): The name or identifier of the model to be used.
        content_type (Optional[Literal["application/json", "text/plain"]]):
            The content type for the agent's input/output. Defaults to "application/json".
        name (Optional[str]): The name of the agent. Defaults to None.
        description (Optional[str]): A brief description of the agent. Defaults to None.
        instructions (Optional[str]): Specific instructions or prompt for the agent. Defaults to None.
        temperature (Optional[float]): A value between 0.0 and 1.0 that controls the randomness of the agent's responses.
            Defaults to None. Must be within the range [0.0, 1.0].
        top_p (Optional[float]): The cumulative probability for nucleus sampling. Defaults to None.
        max_prompt_tokens (Optional[int]): The maximum number of tokens allowed in the prompt. Defaults to None.
        max_completion_tokens (Optional[int]): The maximum number of tokens allowed in the completion. Defaults to None.
        parallel_tool_calls (Optional[bool]): Whether the agent supports parallel tool calls. Defaults to None.
        Notes:
            - The `temperature` attribute controls the randomness of the agent's responses. Lower values make the output more
            deterministic, while higher values increase randomness.
            - The `top_p` attribute is used for nucleus sampling, where the model considers the smallest set of tokens whose
            cumulative probability exceeds the specified value.
            - Future support for truncation strategy and response format is planned.
    """

    model: str
    content_type: Optional[Literal["application/json", "text/plain"]] = "application/json"
    name: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    top_p: Optional[float] = None
    max_prompt_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    parallel_tool_calls: Optional[bool] = None
    # TODO: Add support for truncation strategy and response format
    # truncation_strategy: Optional[TruncationObject] = None
    # response_format: AgentsApiResponseFormatOption | None = None,


# SKAgentConfig - for Semantic Kernel ChatCompletionAgent
class SKAgentConfig(BaseAgentConfig):
    """
    SKAgentConfig is a configuration class that extends the BaseAgentConfig class.
    It provides additional attributes specific to Semantic Kernel (SK) agents.
    Attributes:
        prompt (Optional[str]): The prompt text used by the agent. Defaults to None.
        description (Optional[str]): A brief description of the agent. Defaults to None.
        sk_prompt_execution_settings (Optional[PromptExecutionSettings]):
            Settings related to the execution of the Semantic Kernel prompt. Defaults to None.
    """

    prompt: Optional[str] = None
    description: Optional[str] = None
    sk_prompt_execution_settings: Optional[PromptExecutionSettings] = None


class ChatCompletionAgentConfig(SKAgentConfig):
    type: Literal["ChatCompletionAgentConfig"] = "ChatCompletionAgentConfig"


# AzureAI Agent Config - for Azure AI Foundry agents
class AzureAIAgentConfig(SKAgentConfig):
    """
    AzureAIAgentConfig is a configuration class for an Azure AI Agent.
    Attributes:
        type (Literal["AzureAIAgentConfig"]): Specifies the type of the configuration.
            This is a constant value set to "AzureAIAgentConfig".
        azure_ai_agent_config (AIFoundryAgentConfig): The configuration details specific
            to the AI Foundry Agent.
        search_tool_config (Optional[SearchToolConfig]): An optional configuration for
            the search tool, if applicable.
    """

    type: Literal["AzureAIAgentConfig"] = "AzureAIAgentConfig"
    azure_ai_agent_config: AIFoundryAgentConfig
    search_tool_config: Optional[SearchToolConfig] = None


AgentConfigUnion = Union[AzureAIAgentConfig, ChatCompletionAgentConfig]


class AgentConfig(ConfigBase):
    """
    AgentConfig is a configuration class that inherits from ConfigBase. It represents
    the configuration details specific to an agent.

    Attributes:
        config_type (str): A string representing the type of configuration.
            Defaults to the value of `ConfigType.AGENT.value`.
        config_body (AgentConfigUnion): The body of the agent configuration,
            which can be one of the types defined in the AgentConfigUnion.
    """

    config_type: str = ConfigType.AGENT.value
    config_body: AgentConfigUnion
