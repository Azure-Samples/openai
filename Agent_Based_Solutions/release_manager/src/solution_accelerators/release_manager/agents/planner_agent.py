# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional

from azure.ai.projects import AIProjectClient
from semantic_kernel.agents import AzureAIAgent
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.agent_factory.agent_base import AIFoundryAgentBase
from common.contracts.configuration.agent_config import AzureAIAgentConfig
from common.telemetry.app_logger import AppLogger


class PlannerAgent(AIFoundryAgentBase):
    """
    PlannerAgent helps generate orchestration plans for the Release Manager.
    This agent is designed to be instantiated per session rather than shared.
    """

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        """Initialize the PlannerAgent instance."""
        super().__init__(logger, memory)

    @classmethod
    def _is_singleton(cls) -> bool:
        """
        Override to indicate this agent should use the singleton pattern.

        Returns:
            bool: False, indicating a new instance per session
        """
        return True


    async def _create_foundry_agent(self, configuration: AzureAIAgentConfig, project_client: AIProjectClient) -> AzureAIAgent:
        """
        Create the Planner agent in AI Foundry.

        Args:
            configuration: Agent configuration
            project_client: AI Foundry project client

        Returns:
            The created AI Foundry agent
        """
        if not configuration.azure_ai_agent_config:
            raise ValueError("Azure AI agent configuration is required for Planner Agent.")

        return await super()._create_foundry_agent(configuration, project_client)