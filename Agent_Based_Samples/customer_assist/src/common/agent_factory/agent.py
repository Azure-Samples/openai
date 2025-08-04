# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from abc import ABC, abstractmethod

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import Agent as AIFoundryAgent

from common.contracts.configuration.agent_config import SKAgentConfig


class Agent(ABC):
    @staticmethod
    async def create_agent_from_config(client: AIProjectClient, agent_config: SKAgentConfig) -> AIFoundryAgent:
        """
        Create an agent in Azure AI Foundry from agent configuration.
        """
        try:
            agent = await client.agents.create_agent(**vars(agent_config.azure_ai_agent_config))
            return agent
        except Exception as e:
            print(f"Error creating agent: {e}")
            return None
