# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from typing import Optional

from azure.ai.projects import AIProjectClient
from semantic_kernel import Kernel
from semantic_kernel.agents import AzureAIAgent
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.agent_factory.agent_factory_base import AgentFactory as BaseAgentFactory
from common.contracts.configuration.agent_config import (
    AzureAIAgentConfig,
    ChatCompletionAgentConfig,
)
from common.telemetry.app_logger import AppLogger
from models.devops_settings import DevOpsSettings
from models.jira_settings import JiraSettings

from .planner_agent import PlannerAgent
from .jira_agent import JiraAgent
from .devops_agent import DevOpsAgent
from .visualization_agent import VisualizationAgent
from .fallback_agent import FallbackAgent


class ReleaseManagerAgentFactory:
    """
    Factory class for managing agent creation and reuse in the Release Manager solution.
    Implements a singleton pattern and leverages the base singleton patterns in agent base classes.
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ReleaseManagerAgentFactory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    async def initialize(self, logger: AppLogger, project_client: AIProjectClient, memory: Optional[SemanticTextMemory] = None):
        async with self._lock:
            if self._initialized:
                return

            self.logger = logger
            self.project_client = project_client
            self.memory = memory

            self.base_factory = BaseAgentFactory(logger=self.logger, client=self.project_client)

            self._initialized = True
            self.logger.info("ReleaseManagerAgentFactory initialized")

    async def get_visualization_agent(
        self,
        kernel: Kernel,
        configuration: AzureAIAgentConfig
    ) -> AzureAIAgent:
        """
        Get the Visualization Agent (singleton).
        Leverages the built-in singleton pattern in AIFoundryAgentBase.

        Args:
            kernel: Semantic Kernel instance
            configuration: Resolved agent configuration

        Returns:
            AzureAIAgent: The Visualization Agent instance
        """
        async with self._lock:
            if not self.project_client:
                raise Exception("Project client not initialized. Call get_or_create_project_client first.")

        # The VisualizationAgent class now manages its own singleton state
        visualization_agent = await VisualizationAgent.get_instance(self.logger, self.memory)
        await visualization_agent.initialize(
            kernel=kernel,
            configuration=configuration,
            project_client=self.project_client
        )

        self.logger.info("Visualization Agent initialized or retrieved.")
        return visualization_agent

    async def create_planner_agent(
        self,
        kernel: Kernel,
        configuration: AzureAIAgentConfig
    ) -> AzureAIAgent:
        """
        Create a new instance of PlannerAgent.
        A new instance is created for each orchestrator since PlannerAgent is not a singleton.

        Args:
            kernel: Semantic Kernel instance
            configuration: Resolved agent configuration

        Returns:
            AzureAIAgent: The Planner Agent instance
        """
        # PlannerAgent handles its own instantiation logic based on its _is_singleton() method
        # PlannerAgent is not a singleton, so we create a new instance for each session
        planner_agent = await PlannerAgent.get_instance(self.logger, self.memory)
        await planner_agent.initialize(
            kernel=kernel,
            configuration=configuration,
            project_client=self.project_client
        )

        self.logger.info("Planner Agent initialized or retrieved.")
        return planner_agent

    async def create_jira_agent(
        self,
        kernel: Kernel,
        configuration: ChatCompletionAgentConfig,
        jira_settings: JiraSettings
    ) -> JiraAgent:
        """
        Create a new instance of JiraAgent.
        A new instance is created for each orchestrator since JiraAgent is not a singleton.

        Args:
            kernel: Semantic Kernel instance
            configuration: Resolved agent configuration
            jira_settings: JiraSettings instance containing JIRA server details

        Returns:
            ChatCompletionAgent: A new JIRA agent instance
        """
        # JiraAgent handles its own instantiation logic based on its _is_singleton() method
        # JiraAgent is not a singleton, so we create a new instance for each session
        jira_agent = await JiraAgent.get_instance(self.logger, self.memory)
        await jira_agent.initialize(
            kernel=kernel,
            configuration=configuration,
            server_url=jira_settings.server_url,
            username=jira_settings.username,
            password=jira_settings.password,
            config_file_path=jira_settings.config_file_path
        )

        self.logger.info("Created new JIRA agent instance")
        return jira_agent


    async def create_devops_agent(
        self,
        kernel: Kernel,
        configuration: ChatCompletionAgentConfig,
        devops_settings: DevOpsSettings
    ) -> DevOpsAgent:
        """
        Create a new instance of JiraAgent.
        A new instance is created for each orchestrator since JiraAgent is not a singleton.

        Args:
            kernel: Semantic Kernel instance
            configuration: Resolved agent configuration
            jira_settings: JiraSettings instance containing JIRA server details

        Returns:
            ChatCompletionAgent: A new JIRA agent instance
        """
        # Create DevOpsAgent instance
        devops_agent = await DevOpsAgent.get_instance(self.logger, self.memory)
        await devops_agent.initialize(
            kernel=kernel,
            configuration=configuration,
            server_url=devops_settings.server_url,
            username=devops_settings.username,
            password=devops_settings.password,
            database_name=devops_settings.database_name,
            database_table_name=devops_settings.database_table_name,
            config_file_path=devops_settings.config_file_path
        )

        self.logger.info("Created new DevOps agent instance")
        return devops_agent

    async def create_fallback_agent(
        self,
        kernel: Kernel,
        configuration: ChatCompletionAgentConfig
    ) -> FallbackAgent:
        """
        Create a new instance of FallbackAgent.
        A new instance is created for each orchestrator since FallbackAgent is not a singleton.

        Args:
            kernel: Semantic Kernel instance
            configuration: Resolved agent configuration

        Returns:
            ChatCompletionAgent: A new Fallback agent instance
        """
        # Fallback agent handles its own instantiation logic based on its _is_singleton() method
        # Fallback agent is not a singleton, so we create a new instance for each session
        fallback_agent = await FallbackAgent.get_instance(logger=self.logger)
        await fallback_agent.initialize(
            kernel=kernel,
            configuration=configuration
        )

        self.logger.info("Created new Fallback agent instance")
        return fallback_agent

    async def create_agent_from_config(
        self, kernel: Kernel, configuration: AzureAIAgentConfig | ChatCompletionAgentConfig
    ):
        """
        Create an agent using the base AgentFactory based on configuration type.

        Args:
            kernel: Semantic Kernel instance
            configuration: Agent configuration

        Returns:
            Agent instance based on the configuration type
        """
        if not self.base_factory:
            raise Exception("Base factory not initialized. Call initialize() first.")

        return await self.base_factory.create_agent(configuration=configuration, kernel=kernel)

    @classmethod
    async def get_instance(cls):
        """Get the singleton instance of ReleaseManagerAgentFactory."""
        if not cls._lock:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            if cls._instance is None:
                cls._instance = ReleaseManagerAgentFactory()
        return cls._instance


# For backward compatibility and shorter import statements
AgentFactory = ReleaseManagerAgentFactory
