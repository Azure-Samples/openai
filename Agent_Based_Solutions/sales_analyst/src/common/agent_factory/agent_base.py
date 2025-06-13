# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar, Union

from azure.ai.projects import AIProjectClient
from semantic_kernel import Kernel
from semantic_kernel.agents import (
    AgentThread,
    AzureAIAgent,
    AzureAIAgentThread,
    ChatCompletionAgent,
    ChatHistoryAgentThread,
)
from semantic_kernel.agents.agent import AgentResponseItem
from semantic_kernel.agents.open_ai.run_polling_options import RunPollingOptions
from semantic_kernel.connectors.ai import PromptExecutionSettings
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.kernel import KernelArguments
from semantic_kernel.memory.memory_query_result import MemoryQueryResult
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.contracts.configuration.agent_config import (
    AzureAIAgentConfig,
    ChatCompletionAgentConfig,
    SKAgentConfig,
)
from common.telemetry.app_logger import AppLogger

T = TypeVar("T", bound="AgentBase")


class AgentBase(ABC):
    """Base class for all agents with built-in singleton pattern support."""

    _instances: ClassVar[Dict[Type[T], T]] = {}
    _locks: ClassVar[Dict[Type[T], asyncio.Lock]] = {}

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        self._logger = logger
        self._agent_memory = memory

        self._agent: Optional[Union[ChatCompletionAgent, AzureAIAgent]] = None
        self._kernel: Optional[Kernel] = None
        self._config: Optional[Any] = None
        self._initialized: bool = False

    @classmethod
    def _is_singleton(cls) -> bool:
        return False

    @classmethod
    async def get_instance(cls: Type[T], logger: AppLogger, memory: Optional[SemanticTextMemory] = None) -> T:
        if not cls._is_singleton():
            return cls(logger, memory)

        if cls not in cls._instances:
            if cls not in cls._locks:
                cls._locks[cls] = asyncio.Lock()

            async with cls._locks[cls]:
                if cls not in cls._instances:
                    cls._instances[cls] = cls(logger, memory)

        return cls._instances[cls]

    async def initialize(
        self,
        kernel: Kernel,
        configuration: Union[ChatCompletionAgentConfig, AzureAIAgentConfig],
        project_client: Optional[AIProjectClient] = None,
        **kwargs,
    ) -> Any:
        """
        Initialize the agent with the provided kernel and configuration.

        Args:
            kernel: The kernel to use for the agent.
            configuration: The configuration for the agent. Can be either ChatCompletionAgentConfig or AzureAIAgentConfig.
            project_client: The AIProjectClient for provisioning Azure AI Foundry agents. REQUIRED for AzureAIAgentConfig.
            **kwargs: Additional arguments for agent creation.
        """
        if not self._is_singleton():
            self._initialized = False

        if self._is_singleton() and self._initialized and self._agent:
            return self._agent

        if type(self) not in self._locks:
            self._locks[type(self)] = asyncio.Lock()

        async with self._locks[type(self)]:
            if self._is_singleton() and self._initialized and self._agent:
                return self._agent

            self._kernel = kernel
            self._config = configuration

            if isinstance(configuration, ChatCompletionAgentConfig):
                self._agent = await self._create_sk_agent(configuration, **kwargs)
            elif isinstance(configuration, AzureAIAgentConfig):
                if not project_client:
                    raise ValueError("Project client is required for AzureAIAgentConfig.")

                self._agent = await self._create_foundry_agent(configuration, project_client, **kwargs)
            else:
                raise ValueError("Unsupported agent configuration type.")

            self._initialized = True

            return self._agent

    @abstractmethod
    async def _create_sk_agent(
        self, configuration: Union[AzureAIAgentConfig, ChatCompletionAgentConfig], **kwargs
    ) -> Any:
        pass

    @abstractmethod
    async def _create_foundry_agent(
        self,
        configuration: Union[AzureAIAgentConfig, ChatCompletionAgentConfig],
        project_client: AIProjectClient,
        **kwargs,
    ) -> Any:
        pass

    @abstractmethod
    async def invoke_with_runtime_config(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent],
        thread: AgentThread,
        runtime_config: Optional[Any] = None,
        arguments: Optional[KernelArguments] = None,
    ) -> Any:
        pass

    async def store_memory_in_collection(
        self, collection_name: str, content: str, content_id: str, content_description: Optional[str] = None
    ) -> bool:
        """
        Store information in the agent's memory.

        Args:
            collection_name: The name of the collection to store the information in.
            content: The content to store.
            content_id: Optional ID for the content. If not provided, a unique ID will be generated.
            content_description: Optional description for the content.

        Returns:
            bool: True if the information was successfully stored, False otherwise.
        """
        if not self._agent_memory:
            self._logger.warning("Memory store is not initialized for this agent.")
            return False

        try:
            await self._agent_memory.save_information(
                collection=collection_name,
                id=content_id,
                text=content,
                description=content_description,
            )

            return True
        except Exception as e:
            self._logger.error(f"Failed to store memory for agent {type(self._agent)}: {e}")
            return False

    async def search_memory_in_collection(
        self,
        collection_name: str,
        query: str,
        max_result_count: Optional[int] = 1,
        min_relevance_score: Optional[float] = 0.0,
    ) -> List[MemoryQueryResult]:
        """
        Search for information in the agent's memory.

        Args:
            collection_name: The name of the collection to search in.
            query: The query string to search for.
            max_result_count: Maximum number of results to return. Defaults to 1.
            min_relevance_score: Minimum relevance score for results. Defaults to 0.0.

        Returns:
            List[MemoryQueryResult]: A list of MemoryQueryResult objects containing the search results.
        """
        if not self._agent_memory:
            self._logger.warning("Memory store is not initialized for this agent.")
            return []

        try:
            results: List[MemoryQueryResult] = []
            results = await self._agent_memory.search(
                collection=collection_name,
                query=query,
                limit=max_result_count,
                min_relevance_score=min_relevance_score,
            )

            self._logger.info(
                f"Memory search returned {len(results)} results for query '{query}' in collection '{collection_name}'"
            )
            return results
        except Exception as e:
            self._logger.error(f"Failed to store memory for agent {type(self._agent)}: {e}")
            return False

    def get_agent(self) -> Optional[Any]:
        return self._agent


class SemanticKernelAgentBase(AgentBase):
    """Implementation for Semantic Kernel based agents."""

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        super().__init__(logger, memory)

    async def _create_sk_agent(self, configuration: ChatCompletionAgentConfig, **kwargs) -> ChatCompletionAgent:
        prompt = configuration.prompt
        agent_name = configuration.agent_name
        arguments = None
        settings = configuration.sk_prompt_execution_settings or PromptExecutionSettings()

        if kwargs.get("response_format"):
            settings.extension_data["response_format"] = kwargs.get("response_format")

        arguments = KernelArguments(settings=configuration.sk_prompt_execution_settings)

        return ChatCompletionAgent(
            kernel=self._kernel,
            name=agent_name,
            instructions=prompt,
            arguments=arguments,
            description=configuration.description,
        )

    async def _create_foundry_agent(
        self, configuration: AzureAIAgentConfig, project_client: AIProjectClient, **kwargs
    ) -> AzureAIAgent:
        raise NotImplementedError("Foundry agent creation is not supported in SemanticKernelAgentBase.")

    async def invoke_with_runtime_config(
        self,
        kernel: Kernel,
        messages: str | ChatMessageContent | list[str | ChatMessageContent],
        thread: ChatHistoryAgentThread,
        runtime_config: Optional[SKAgentConfig] = None,
        arguments: Optional[KernelArguments] = None,
    ) -> AgentResponseItem[ChatMessageContent]:
        if not self._agent:
            raise ValueError("Agent not initialized. Call initialize() first.")

        kernel_args = arguments or KernelArguments()

        if runtime_config and runtime_config.sk_prompt_execution_settings:
            kernel_args = KernelArguments(settings=runtime_config.sk_prompt_execution_settings)

        return await self._agent.get_response(
            kernel=kernel,
            messages=messages,
            thread=thread,
            arguments=kernel_args,
        )


class AIFoundryAgentBase(AgentBase):
    """Implementation for Azure AI Foundry agents."""

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        super().__init__(logger, memory)
        self._client: AIProjectClient = None

    async def _create_foundry_agent(
        self, configuration: AzureAIAgentConfig, project_client: AIProjectClient, **kwargs
    ) -> AzureAIAgent:
        if not project_client:
            raise ValueError("Project client is required for AIFoundryAgentBase.")

        self._client = project_client

        # Create the agent in Foundry - this should be implemented by subclasses
        foundry_agent = await self._client.agents.create_agent(
            model=configuration.azure_ai_agent_config.model,
            name=configuration.agent_name,
            instructions=configuration.azure_ai_agent_config.instructions,
            temperature=configuration.azure_ai_agent_config.temperature,
            top_p=configuration.azure_ai_agent_config.top_p,
            description=configuration.azure_ai_agent_config.description,
            tools=kwargs.get("tools", []),
            tool_resources=kwargs.get("tool_resources", None),
            response_format=kwargs.get("response_format", None),
        )

        # Create and store the SK agent wrapper
        self._agent = AzureAIAgent(
            kernel=self._kernel,
            client=project_client,
            definition=foundry_agent,
            polling_options=RunPollingOptions(run_polling_timeout=timedelta(minutes=2)),  # 2mins for Foundry agents
        )

        self._initialized = True
        return self._agent

    async def _create_sk_agent(
        self, configuration: Union[AzureAIAgentConfig, ChatCompletionAgentConfig], **kwargs
    ) -> Any:
        raise NotImplementedError("SK agent creation is not supported in AIFoundryAgentBase.")

    async def invoke_with_runtime_config(
        self,
        kernel: Kernel,
        messages: str | ChatMessageContent | list[str | ChatMessageContent],
        thread: AzureAIAgentThread,
        runtime_config: Optional[AzureAIAgentConfig] = None,
        arguments: Optional[KernelArguments] = None,
    ) -> AgentResponseItem[ChatMessageContent]:
        """
        Run the agent with configuration provided at runtime.

        Args:
            messages: The messages to send to the agent
            thread: The thread to use for this run
            runtime_config: Configuration to use for this specific run
            kernel: The kernel to use for this run

        Returns:
            The result from agent.get_response()
        """
        if not self._agent or not self._client:
            raise ValueError("Agent not initialized. Call initialize() first.")

        response = await self._agent.get_response(
            messages=messages,
            thread=thread,
            temperature=runtime_config.azure_ai_agent_config.temperature if runtime_config else None,
            top_p=runtime_config.azure_ai_agent_config.top_p if runtime_config else None,
            max_prompt_tokens=runtime_config.azure_ai_agent_config.max_completion_tokens if runtime_config else None,
            max_completion_tokens=runtime_config.azure_ai_agent_config.max_prompt_tokens if runtime_config else None,
            parallel_tool_calls=runtime_config.azure_ai_agent_config.parallel_tool_calls if runtime_config else None,
            kernel=kernel,
            arguments=arguments,
        )

        return response
