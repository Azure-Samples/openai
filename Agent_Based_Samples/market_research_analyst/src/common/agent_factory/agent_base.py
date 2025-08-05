# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar, Union

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import RunStatus, ThreadRun, MessageRole, Agent as AIFoundryAgent
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
    AIFoundryAgentConfig,
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

        self._agent: Optional[Union[ChatCompletionAgent, AzureAIAgent, AIFoundryAgent]] = None
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
        configuration: Union[ChatCompletionAgentConfig, AzureAIAgentConfig, AIFoundryAgentConfig],
        project_client: Optional[AIProjectClient] = None,
        kernel: Optional[Kernel] = None,
        **kwargs,
    ) -> Any:
        """
        Initialize the agent with the provided configuration and optional kernel.

        Args:
            configuration: The configuration for the agent. Can be either ChatCompletionAgentConfig, AzureAIAgentConfig, or AIFoundryAgentConfig.
            project_client: The AIProjectClient for provisioning Azure AI Foundry agents. REQUIRED for AzureAIAgentConfig and AIFoundryAgentConfig.
            kernel: The kernel to use for the agent, only required if using Semantic Kernel based agents.
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
                if not kernel:
                    raise ValueError("Kernel is required for ChatCompletionAgentConfig.")
                self._agent = await self._create_chat_completion_agent(configuration, **kwargs)
            elif isinstance(configuration, AzureAIAgentConfig):
                if not project_client:
                    raise ValueError("Project client is required for AzureAIAgent.")
                if not kernel:
                    raise ValueError("Kernel is required for AIFoundryAgentConfig.")
                self._agent = await self._create_azure_ai_agent(configuration, project_client, **kwargs)
            elif isinstance(configuration, AIFoundryAgentConfig):
                if not project_client:
                    raise ValueError("Project client is required for AIFoundryAgent.")
                self._agent = await self._create_foundry_agent(configuration, project_client, **kwargs)
            else:
                raise ValueError("Unsupported agent configuration type.")

            self._initialized = True

            return self._agent

    @abstractmethod
    async def _create_chat_completion_agent(
        self, configuration: ChatCompletionAgentConfig, **kwargs
    ) -> ChatCompletionAgent:
        """Create a ChatCompletion agent using Semantic Kernel."""
        pass

    @abstractmethod
    async def _create_azure_ai_agent(
        self,
        configuration: AIFoundryAgentConfig,
        project_client: AIProjectClient,
        **kwargs,
    ) -> AzureAIAgent:
        """Create an Azure AI agent in Foundry using Semantic Kernel."""
        pass

    @abstractmethod
    async def _create_foundry_agent(
        self,
        configuration: AzureAIAgentConfig,
        project_client: AIProjectClient,
        **kwargs,
    ) -> Any:
        """Create an agent in Azure AI Foundry using AIProjectClient."""
        pass

    @abstractmethod
    async def invoke_with_runtime_config(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent],
        thread: AgentThread,
        runtime_config: Optional[Any] = None,
        **kwargs,
    ) -> Any:
        pass

    def get_agent(self) -> Optional[Any]:
        return self._agent


class SemanticKernelAgentBase(AgentBase):
    """Base class for agents that require a Semantic Kernel instance."""

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        super().__init__(logger, memory)

    @abstractmethod
    async def invoke_with_runtime_config(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent],
        thread: AgentThread,
        kernel: Kernel = None,
        runtime_config: Optional[Any] = None,
        arguments: Optional[KernelArguments] = None,
    ) -> Any:
        pass

    async def _create_foundry_agent(
        self,
        configuration: AzureAIAgentConfig,
        project_client: AIProjectClient,
        **kwargs,
    ) -> Any:
        raise NotImplementedError("Foundry agent creation is not supported in SemanticKernelAgentBase.")

    async def store_memory_in_collection(
        self,
        collection_name: str,
        content: str,
        content_id: str,
        content_description: Optional[str] = None,
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


class ChatCompletionAgentBase(SemanticKernelAgentBase):
    """
    Base class for agents that use chat completion APIs managed through Semantic Kernel.

    This class provides a pure Semantic Kernel approach to agent creation and management,
    utilizing chat completion APIs (like OpenAI, Azure OpenAI, or other compatible services)
    as the underlying intelligence layer. The agents are created, configured, and orchestrated
    entirely through Semantic Kernel's ChatCompletionAgent.

    Key Features:
    - Pure Semantic Kernel agent implementation using ChatCompletionAgent
    - Support for any chat completion API compatible with SK
    - Full SK ecosystem integration (plugins, functions, memory)
    - Flexible execution settings and response format control
    - Built-in conversation management through SK threads
    """

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        super().__init__(logger, memory)

    async def _create_chat_completion_agent(
        self, configuration: ChatCompletionAgentConfig, **kwargs
    ) -> ChatCompletionAgent:
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

    async def _create_azure_ai_agent(
        self,
        configuration: AIFoundryAgentConfig,
        project_client: AIProjectClient,
        **kwargs,
    ) -> AzureAIAgent:
        raise NotImplementedError("Foundry agent creation is not supported in SemanticKernelAgentBase.")

    async def _create_foundry_agent(
        self,
        configuration: AzureAIAgentConfig,
        project_client: AIProjectClient,
        **kwargs,
    ) -> Any:
        raise NotImplementedError("Azure agent creation is not supported in SemanticKernelAgentBase.")

    async def invoke_with_runtime_config(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent],
        thread: ChatHistoryAgentThread,
        kernel: Optional[Kernel] = None,
        runtime_config: Optional[SKAgentConfig] = None,
        arguments: Optional[KernelArguments] = None,
        **kwargs: Any,
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


class AzureAIAgentBase(SemanticKernelAgentBase):
    """
    Base class for Azure AI Foundry agents managed through Semantic Kernel.

    This class provides a hybrid approach for working with Azure AI Foundry agents by combining
    the power of Azure AI Foundry's native agent capabilities with Semantic Kernel's orchestration
    and management features. The agents are created in Azure AI Foundry but are configured,
    managed, and invoked through Semantic Kernel APIs.

    Key Features:
    - Agents are created directly in Azure AI Foundry platform using AIProjectClient
    - Agent lifecycle (configuration, invocation) is managed through Semantic Kernel
    - Combines Foundry's native agent capabilities with SK's orchestration features
    - Built-in support for Semantic Kernel kernels, plugins, and memory systems
    - Advanced conversation management through AzureAIAgentThread
    - Runtime configuration overrides with full SK integration
    - Automatic polling and status management for long-running operations
    """

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        super().__init__(logger, memory)
        self._client: AIProjectClient = None

    async def _create_azure_ai_agent(
        self,
        configuration: AzureAIAgentConfig,
        project_client: AIProjectClient,
        **kwargs,
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

    async def _create_chat_completion_agent(self, configuration: ChatCompletionAgentConfig, **kwargs) -> Any:
        raise NotImplementedError("SK agent creation is not supported in AIFoundryAgentBase.")

    async def _create_foundry_agent(
        self,
        configuration: AzureAIAgentConfig,
        project_client: AIProjectClient,
        **kwargs,
    ) -> Any:
        raise NotImplementedError("Azure agent creation is not supported in AIFoundryAgentBase.")

    async def invoke_with_runtime_config(
        self,
        messages: str | ChatMessageContent | list[str | ChatMessageContent],
        thread: AzureAIAgentThread,
        kernel: Optional[Kernel] = None,
        runtime_config: Optional[AzureAIAgentConfig] = None,
        arguments: Optional[KernelArguments] = None,
        **kwargs: Any,
    ) -> AgentResponseItem[ChatMessageContent]:
        if not self._agent or not self._client:
            raise ValueError("Agent not initialized. Call initialize() first.")

        response = await self._agent.get_response(
            messages=messages,
            thread=thread,
            temperature=(runtime_config.azure_ai_agent_config.temperature if runtime_config else None),
            top_p=(runtime_config.azure_ai_agent_config.top_p if runtime_config else None),
            max_prompt_tokens=(runtime_config.azure_ai_agent_config.max_completion_tokens if runtime_config else None),
            max_completion_tokens=(runtime_config.azure_ai_agent_config.max_prompt_tokens if runtime_config else None),
            parallel_tool_calls=(runtime_config.azure_ai_agent_config.parallel_tool_calls if runtime_config else None),
            kernel=kernel,
            arguments=arguments,
        )

        return response


class AzureAIFoundryAgentBase(AgentBase):
    """
    Base class for creating and managing agents directly in Azure AI Foundry.

    This class is designed for creating agents directly in Azure AI Foundry using the AIProjectClient
    and invoking them through native Foundry APIs. Unlike other agent base classes, this does NOT
    require Semantic Kernel - making it ideal for scenarios where you want to:

    - Create agents directly in Azure AI Foundry platform
    - Orchestrate agents using native Foundry capabilities
    - Leverage native Foundry features like advanced tool integration
    - Use Foundry's built-in conversation management using Thread

    Usage:
        This class should be subclassed to implement specific agent behaviors.
        The agent is created and managed entirely within Azure AI Foundry,
        providing access to all platform-native features and optimizations.
    """

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        super().__init__(logger, memory)
        self._client: AIProjectClient = None
        self._logger = logger

    async def _create_foundry_agent(
        self,
        configuration: AIFoundryAgentConfig,
        project_client: AIProjectClient,
        **kwargs,
    ) -> Any:
        if not project_client:
            raise ValueError("Project client is required for AzureAgentBase.")

        self._client = project_client

        # Create the agent in Azure AI
        self._agent = await self._client.agents.create_agent(
            model=configuration.model,
            name=configuration.name,
            instructions=configuration.instructions,
            temperature=configuration.temperature,
            top_p=configuration.top_p,
            description=configuration.description,
            tools=kwargs.get("tools", []),
            tool_resources=kwargs.get("tool_resources", None),
            response_format=kwargs.get("response_format", None),
        )

        self._initialized = True
        return self._agent

    async def _create_chat_completion_agent(self, configuration: ChatCompletionAgentConfig, **kwargs) -> Any:
        raise NotImplementedError("SK agent creation is not supported in AzureAgentBase.")

    async def _create_azure_ai_agent(
        self,
        configuration: AIFoundryAgentConfig,
        project_client: AIProjectClient,
        **kwargs,
    ) -> Any:
        raise NotImplementedError("Foundry agent creation is not supported in AzureAgentBase.")

    async def invoke_with_runtime_config(
        self,
        messages: str,
        thread: AgentThread,
        runtime_config: Optional[AIFoundryAgentConfig] = None,
        project_client: Optional[AIProjectClient] = None,
        **kwargs,
    ) -> str:
        if not self._agent or not self._client:
            raise ValueError("Agent not initialized. Call initialize() first.")

        client: AIProjectClient = project_client or self._client

        # Add user message to the conversation thread
        await client.messages.create(thread_id=thread.id, role=MessageRole.USER, content=messages)

        # Create and process the agent run with optional runtime overrides
        run: ThreadRun = await client.agents.runs.create_and_process(
            thread_id=thread.id,
            agent_id=self._agent.id,
            instructions=runtime_config.instructions if runtime_config else None,
            temperature=runtime_config.temperature if runtime_config else None,
            top_p=runtime_config.top_p if runtime_config else None,
            max_prompt_tokens=(runtime_config.max_prompt_tokens if runtime_config else None),
            max_completion_tokens=(runtime_config.max_completion_tokens if runtime_config else None),
            parallel_tool_calls=(runtime_config.parallel_tool_calls if runtime_config else None),
        )

        # Verify successful completion
        if run.status != RunStatus.COMPLETED:
            self._logger.error(f"Azure AI agent run failed with status: {run.status}")
            raise RuntimeError(f"Azure AI agent run failed with status: {run.status}")

        # Retrieve the agent's response from the thread
        last_msg = await client.messages.get_last_message_text_by_role(thread_id=thread.id, role=MessageRole.AGENT)

        if last_msg:
            return last_msg.text.value

        self._logger.error("No response received from the agent.")
        raise RuntimeError("No response received from the agent.")
