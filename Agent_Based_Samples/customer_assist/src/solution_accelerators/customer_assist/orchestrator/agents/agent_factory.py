# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from typing import Optional, Dict, Any
from semantic_kernel.kernel import Kernel
from azure.ai.projects import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from azure.core.exceptions import AzureError

from semantic_kernel.agents import AzureAIAgent
from common.contracts.configuration.agent_config import AzureAIAgentConfig, ChatCompletionAgentConfig
from common.telemetry.app_logger import AppLogger
from common.agent_factory.agent_factory_base import AgentFactory as BaseAgentFactory
from .process_conversation_agent import AssistantAgent
from .sentiment_analysis_agent import LocalSentimentAnalysisAgent, SentimentAnalysisAgent
from .post_call_analysis_agent import PostCallAnalysisAgent


class CustomerCallAssistAgentFactory:
    """Factory for creating agents used in the Customer Call Assist solution.

    This class implements the singleton pattern to ensure only one instance of the factory
    exists throughout the application lifecycle. It manages the creation and initialization
    of various specialized agents for customer call processing.

    Attributes:
        logger (AppLogger): Logger instance for tracking factory operations
        project_client (Optional[AIProjectClient]): Azure AI Project client instance
        base_factory (Optional[BaseAgentFactory]): Base agent factory instance
    """

    _instance: Optional["CustomerCallAssistAgentFactory"] = None
    _lock = asyncio.Lock()
    _logger: Optional[AppLogger] = None
    _initialization_timeout = 30  # seconds

    def __new__(cls) -> "CustomerCallAssistAgentFactory":
        if cls._instance is None:
            cls._instance = super(CustomerCallAssistAgentFactory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    async def __init_async__(self, logger: AppLogger) -> None:
        """Initialize the factory asynchronously.

        Args:
            logger: AppLogger instance for logging factory operations

        Raises:
            TimeoutError: If initialization takes longer than the timeout period
            RuntimeError: If initialization fails
        """
        try:
            async with asyncio.timeout(self._initialization_timeout):
                async with self._lock:
                    if self._initialized:
                        return

                    self.logger = logger
                    self.project_client: Optional[AIProjectClient] = None
                    self.base_factory: Optional[BaseAgentFactory] = None
                    self._initialized = True
                    self.logger.info("CustomerCallAssistAgentFactory initialized")
        except asyncio.TimeoutError:
            self.logger.error("Factory initialization timed out")
            raise TimeoutError("Factory initialization exceeded timeout period")
        except Exception as e:
            self.logger.error(f"Factory initialization failed: {str(e)}")
            raise RuntimeError(f"Failed to initialize factory: {str(e)}")

    async def initialize_project_client(self) -> AIProjectClient:
        """Initialize the Azure AI Project client if not already initialized.

        Returns:
            AIProjectClient: The initialized project client

        Raises:
            AzureError: If client initialization fails
        """
        async with self._lock:
            if not self.project_client:
                try:
                    self.project_client = AzureAIAgent.create_client(credential=DefaultAzureCredential())
                    self.logger.info("Project client initialized")

                    self.base_factory = BaseAgentFactory(client=self.project_client, logger=self.logger)
                    self.logger.info("Base Agent factory initialized")
                except AzureError as e:
                    self.logger.error(f"Failed to initialize project client: {str(e)}")
                    raise

        return self.project_client

    async def get_assistant_agent(self, kernel: Kernel, configuration: AzureAIAgentConfig) -> AssistantAgent:
        """Create and initialize an assistant agent instance.

        Args:
            kernel: Semantic kernel instance
            configuration: Agent configuration parameters

        Returns:
            AssistantAgent: Initialized assistant agent
        """
        self.logger.info("Initializing assistant agent")
        try:
            agent: AssistantAgent = await AssistantAgent.get_instance(logger=self.logger)
            await self.initialize_project_client()
            await agent.initialize(kernel=kernel, configuration=configuration, project_client=self.project_client)
            self.logger.info("Assistant agent initialized successfully")
            return agent
        except Exception as e:
            self.logger.error(f"Failed to initialize assistant agent: {str(e)}")
            raise RuntimeError(f"Assistant agent initialization failed: {str(e)}")

    async def get_sentiment_agent(self, kernel: Kernel, configuration: AzureAIAgentConfig) -> SentimentAnalysisAgent:
        """Create and initialize a sentiment analysis agent instance.

        Args:
            kernel: Semantic kernel instance
            configuration: Agent configuration parameters

        Returns:
            SentimentAnalysisAgent: Initialized sentiment analysis agent

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If agent initialization fails
        """
        self.logger.info("Initializing sentiment analysis agent")
        try:
            if isinstance(configuration, AzureAIAgentConfig):
                agent: SentimentAnalysisAgent = await SentimentAnalysisAgent.get_instance(logger=self.logger)
                await self.initialize_project_client()
                await agent.initialize(kernel=kernel, configuration=configuration, project_client=self.project_client)
                self.logger.info("Sentiment analysis agent initialized successfully")
                return agent
            elif isinstance(configuration, ChatCompletionAgentConfig):
                agent: LocalSentimentAnalysisAgent = await LocalSentimentAnalysisAgent.get_instance(logger=self.logger)
                await agent.initialize(kernel=kernel, configuration=configuration)
                self.logger.info("Local Sentiment analysis agent initialized successfully")
                return agent
            else:
                raise ValueError("Invalid configuration type for sentiment analysis agent")
        except ValueError as ve:
            self.logger.error(f"Invalid configuration for sentiment analysis agent: {str(ve)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize sentiment analysis agent: {str(e)}")
            raise RuntimeError(f"Sentiment agent initialization failed: {str(e)}")

    async def get_post_call_agent(self, kernel: Kernel, configuration: AzureAIAgentConfig) -> PostCallAnalysisAgent:
        """Create and initialize a post-call analysis agent instance.

        Args:
            kernel: Semantic kernel instance
            configuration: Agent configuration parameters

        Returns:
            PostCallAnalysisAgent: Initialized post-call analysis agent

        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If agent initialization fails
        """
        self.logger.info("Initializing post-call analysis agent")
        try:
            agent: PostCallAnalysisAgent = await PostCallAnalysisAgent.get_instance(logger=self.logger)
            await self.initialize_project_client()
            await agent.initialize(kernel=kernel, configuration=configuration, project_client=self.project_client)
            self.logger.info("Post-call analysis agent initialized successfully")
            return agent
        except Exception as e:
            self.logger.error(f"Failed to initialize post-call analysis agent: {str(e)}")
            raise RuntimeError(f"Post-call agent initialization failed: {str(e)}")

    @classmethod
    async def reset(cls) -> None:
        """Reset the factory instance (primarily for testing purposes)."""
        async with cls._lock:
            cls._instance = None
            cls._logger = None

    @classmethod
    async def get_instance(cls) -> "CustomerCallAssistAgentFactory":
        """Get the singleton instance of CustomerCallAssistAgentFactory.

        Returns:
            CustomerCallAssistAgentFactory: The singleton factory instance
        """
        if not cls._lock:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            if cls._instance is None:
                cls._instance = CustomerCallAssistAgentFactory()
        return cls._instance


# Maintain backward compatibility
AgentFactory = CustomerCallAssistAgentFactory
