# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional

from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool, ToolSet, CodeInterpreterTool, RunStatus, ToolOutput, BingGroundingTool
from semantic_kernel.agents import AzureAIAgent
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.agent_factory.agent_base import AIFoundryAgentBase
from common.contracts.configuration.agent_config import AzureAIAgentConfig
from common.telemetry.app_logger import AppLogger
from config.default_config import DefaultConfig


class SalesAnalystAgent(AIFoundryAgentBase):
    """
    Singleton implementation of SalesAnalystAgent.
    This agent is shared across all AgentOrchestrator instances.
    Extends AIFoundryAgentBase to leverage built-in singleton support.
    """

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        """Initialize the SalesAnalystAgent instance."""
        super().__init__(logger, memory)
        self._user_arguments = {}

    @classmethod
    def _is_singleton(cls) -> bool:
        """
        Override to indicate this agent should use the singleton pattern.

        Returns:
            bool: Always True for SalesAnalystAgent
        """
        return True

    async def _create_foundry_agent(
        self, configuration: AzureAIAgentConfig, project_client: AIProjectClient
    ) -> AzureAIAgent:
        """
        Create the Sales Analyst agent in AI Foundry.

        Args:
            configuration: Agent configuration

        Returns:
            The created AI Foundry agent
        """
        if not configuration.azure_ai_agent_config:
            raise ValueError("Azure AI agent configuration is required for SalesAnalystAgent.")

        code_interpreter = CodeInterpreterTool()
        connections = project_client.connections.list()
        bing_connection_id = None
        async for conn in connections:
            if conn.name == DefaultConfig.AZURE_AI_BING_GROUNDING_CONNECTION_NAME:
                bing_connection_id = conn.id
                break

        toolset = ToolSet()
        toolset.add(code_interpreter)
        toolset.add(BingGroundingTool(connection_id=bing_connection_id))

        return await super()._create_foundry_agent(
            configuration=configuration,
            project_client=project_client,
            tools=toolset.definitions,
            tool_resources=toolset.resources,
        )

    async def update_arguments(self, **kwargs):
        """
        Update the user arguments for the agent.

        Args:
            **kwargs: User arguments to be passed to the agent
        """
        self._user_arguments.update(kwargs)
