# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import List, Optional
from azure.ai.projects.models import Agent
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ResponseFormatJsonSchema, ResponseFormatJsonSchemaType
from semantic_kernel.agents import AzureAIAgent
from common.agent_factory.agent_base import AIFoundryAgentBase
from common.contracts.configuration.agent_config import AIFoundryAgentConfig, AzureAIAgentConfig
from models.step_responses import AdvisorInsights
from azure.ai.projects.models import ConnectionType, ConnectionProperties, AzureAISearchTool, AzureAISearchQueryType


class AssistantAgent(AIFoundryAgentBase):
    """Agent for processing and analyzing conversations."""

    @classmethod
    def _is_singleton(cls) -> bool:
        return True

    async def _create_foundry_agent(self, configuration: AzureAIAgentConfig, project_client: AIProjectClient) -> Agent:
        """Create the conversation processing agent in AI Foundry."""

        # Add search tool to the agent
        if configuration.search_tool_config:
            conn_list: List[ConnectionProperties] = await project_client.connections.list()
            if not conn_list:
                self._logger.error("No connections found in the AIProjectClient.")

            # Find Azure AI Search connection
            ai_search_conn_id = None
            for conn in conn_list:
                if conn.connection_type == ConnectionType.AZURE_AI_SEARCH and conn.authentication_type == "AAD":
                    ai_search_conn_id = conn.id
                    break

            if not ai_search_conn_id:
                self._logger.error("No valid Azure AI Search connection with AAD authentication found.")

            # Create Azure AI Search tool
            loan_policy_search = AzureAISearchTool(
                index_connection_id=ai_search_conn_id,
                index_name=configuration.search_tool_config.index_name,
                query_type=AzureAISearchQueryType.SEMANTIC,
            )
            tools = loan_policy_search.definitions
            tool_resources = loan_policy_search.resources

        return await super()._create_foundry_agent(
            configuration=configuration,
            project_client=project_client,
            response_format=ResponseFormatJsonSchemaType(
                json_schema=ResponseFormatJsonSchema(
                    name="advisor_insights",
                    description="Extract insights for advisor for pending tasks.",
                    schema=AdvisorInsights.model_json_schema(),
                )
            ),
            tools=tools,
            tool_resources=tool_resources,
        )

    async def invoke_with_runtime_config(self, messages, thread, runtime_config=None, kernel=None):
        return await super().invoke_with_runtime_config(
            messages=messages, thread=thread, runtime_config=runtime_config, kernel=kernel
        )
