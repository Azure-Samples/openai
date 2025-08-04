# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
from typing import Optional

from azure.ai.projects import AIProjectClient
from semantic_kernel import Kernel
from semantic_kernel.agents import AzureAIAgent

from common.agent_factory.agent_factory_base import AgentFactory as BaseAgentFactory
from common.contracts.configuration.agent_config import (
    AzureAIAgentConfig,
    ChatCompletionAgentConfig,
)
from common.telemetry.app_logger import AppLogger

from .sales_analyst_agent import SalesAnalystAgent


class SalesAnalystAgentFactory:
    """
    Factory class for managing agent creation and reuse in the Sales Analyst solution.
    Implements a singleton pattern and leverages the base singleton patterns in agent base classes.
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SalesAnalystAgentFactory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    async def initialize(self, logger: AppLogger, project_client: AIProjectClient):
        async with self._lock:
            if self._initialized:
                return

            self.logger = logger
            self.project_client = project_client

            self.base_factory = BaseAgentFactory(logger=self.logger, client=self.project_client)

            self._initialized = True
            self.logger.info("SalesAnalystAgentFactory initialized")

    async def get_sales_analyst_agent(self, kernel: Kernel, configuration: AzureAIAgentConfig) -> AzureAIAgent:
        """
        Get the Sales Analyst Agent (singleton).
        Leverages the built-in singleton pattern in AIFoundryAgentBase.

        Args:
            kernel: Semantic Kernel instance
            configuration: Resolved agent configuration

        Returns:
            AzureAIAgent: The Sales Analyst Agent instance
        """
        async with self._lock:
            if not self.project_client:
                raise Exception("Project client not initialized. Call get_or_create_project_client first.")

        sales_analyst_agent = await SalesAnalystAgent.get_instance(self.logger)
        await sales_analyst_agent.initialize(
            kernel=kernel, configuration=configuration, project_client=self.project_client
        )

        self.logger.info("Sales Analyst Agent initialized or retrieved.")
        return sales_analyst_agent

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
        """Get the singleton instance of SalesAnalystAgentFactory."""
        if not cls._lock:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            if cls._instance is None:
                cls._instance = SalesAnalystAgentFactory()
        return cls._instance


# For backward compatibility and shorter import statements
AgentFactory = SalesAnalystAgentFactory
