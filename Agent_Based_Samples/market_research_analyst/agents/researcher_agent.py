# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional

from azure.ai.agents.models import BingGroundingTool
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.agent_factory.agent_base import AzureAIAgentBase
from common.contracts.configuration.agent_config import AzureAIAgentConfig
from common.telemetry.app_logger import AppLogger


class ResearcherAgent(AzureAIAgentBase):
    """
    ResearcherAgent helps generate detailed research text for the Market Research Analyst assistant.
    This agent is designed to be shared across sessions.
    """

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        """Initialize the ResearcherAgent instance."""
        super().__init__(logger, memory)

    @classmethod
    def _is_singleton(cls) -> bool:
        """
        Override to indicate this agent should use the singleton pattern.

        Returns:
            bool: False, indicating a new instance per session
        """
        return True

    async def _create_azure_ai_agent(
        self,
        configuration: AzureAIAgentConfig,
        project_client: AIProjectClient,
        bing_connection_id: str,
    ) -> AzureAIAgent:
        """
        Create the Researcher agent in AI Foundry.

        Args:
            configuration: Agent configuration
            project_client: AI Foundry project client

        Returns:
            The created AI Foundry agent
        """
        # Add Custom Bing Grounding Tool for Researcher Agent
        bing_grounding_connection_id = None
        async for conn in project_client.connections.list():
            if conn.name == bing_connection_id:
                bing_grounding_connection_id = conn.id
                break

        if not bing_grounding_connection_id:
            raise ValueError("Bing connection ID is required for Researcher Agent.")

        if not configuration.azure_ai_agent_config:
            raise ValueError("Azure AI agent configuration is required for Researcher Agent.")

        bing_grounding_tool = BingGroundingTool(connection_id=bing_grounding_connection_id)

        return await super()._create_azure_ai_agent(
            configuration=configuration,
            project_client=project_client,
            tools=bing_grounding_tool.definitions,
            tool_resources=bing_grounding_tool.resources,
        )
