# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from typing import Optional

from azure.ai.projects import AIProjectClient
from semantic_kernel import Kernel
from semantic_kernel.agents import AzureAIAgent
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.agent_factory.agent_factory_base import AgentFactory as BaseAgentFactory
from common.contracts.configuration.agent_config import AzureAIAgentConfig
from common.telemetry.app_logger import AppLogger

from .report_comparator_agent import ReportComparatorAgent
from .report_generator_agent import ReportGeneratorAgent
from .researcher_agent import ResearcherAgent
from .search_query_generator_agent import SearchQueryGeneratorAgent


class MarketResearchAnalystAgentFactory:
    """
    Factory class for managing agent creation and reuse in the Market Research Analyst solution.
    Implements a singleton pattern and leverages the base singleton patterns in agent base classes.
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MarketResearchAnalystAgentFactory, cls).__new__(cls)
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
            self.logger.info("MarketResearchAnalystAgentFactory initialized")

    async def create_search_query_generator_agent(
        self,
        kernel: Kernel,
        configuration: AzureAIAgentConfig,
    ) -> AzureAIAgent:
        """
        Create a new instance of Search Query Generator Agent.

        Args:
            kernel: Semantic Kernel instance
            configuration: Resolved agent configuration

        Returns:
            AzureAIAgent: The Search Query Generator Agent instance
        """
        search_query_generator_agent = await SearchQueryGeneratorAgent.get_instance(self.logger, self.memory)
        await search_query_generator_agent.initialize(
            kernel=kernel,
            configuration=configuration,
            project_client=self.project_client
        )

        self.logger.info("Search Query Generator Agent initialized or retrieved.")
        return search_query_generator_agent

    async def create_researcher_agent(
        self,
        kernel: Kernel,
        configuration: AzureAIAgentConfig,
        bing_connection_id: str
    ) -> AzureAIAgent:
        """
        Create a new instance of ResearcherAgent.

        Args:
            kernel: Semantic Kernel instance
            configuration: Resolved agent configuration
            bing_connection_id: Bing connection ID for grounding

        Returns:
            AzureAIAgent: The Researcher Agent instance
        """
        researcher_agent = await ResearcherAgent.get_instance(self.logger, self.memory)
        await researcher_agent.initialize(
            kernel=kernel,
            configuration=configuration,
            project_client=self.project_client,
            bing_connection_id=bing_connection_id
        )

        self.logger.info("Researcher Agent initialized or retrieved.")
        return researcher_agent

    async def create_report_generator_agent(
        self,
        kernel: Kernel,
        configuration: AzureAIAgentConfig
    ) -> AzureAIAgent:
        """
        Create a new instance of Report Generator Agent.

        Args:
            kernel: Semantic Kernel instance
            configuration: Resolved agent configuration

        Returns:
            AzureAIAgent: The Report Generator Agent instance
        """
        report_generator_agent = await ReportGeneratorAgent.get_instance(self.logger, self.memory)
        await report_generator_agent.initialize(
            kernel=kernel,
            configuration=configuration,
            project_client=self.project_client
        )

        self.logger.info("Report Generator Agent initialized or retrieved.")
        return report_generator_agent

    async def create_report_comparator_agent(
        self,
        kernel: Kernel,
        configuration: AzureAIAgentConfig,
        bing_connection_id: str
    ) -> AzureAIAgent:
        """
        Create a new instance of Report Comparator Agent.

        Args:
            kernel: Semantic Kernel instance
            configuration: Resolved agent configuration
            bing_connection_id: Bing connection ID for grounding

        Returns:
            AzureAIAgent: The Report Comparator Agent instance
        """
        report_comparator_agent = await ReportComparatorAgent.get_instance(self.logger, self.memory)
        await report_comparator_agent.initialize(
            kernel=kernel,
            configuration=configuration,
            project_client=self.project_client,
            bing_connection_id=bing_connection_id
        )

        self.logger.info("Report Comparator Agent initialized or retrieved.")
        return report_comparator_agent

    @classmethod
    async def get_instance(cls):
        """Get the singleton instance of MarketResearchAnalystAgentFactory."""
        if not cls._lock:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            if cls._instance is None:
                cls._instance = MarketResearchAnalystAgentFactory()
        return cls._instance


# For backward compatibility and shorter import statements
AgentFactory = MarketResearchAnalystAgentFactory