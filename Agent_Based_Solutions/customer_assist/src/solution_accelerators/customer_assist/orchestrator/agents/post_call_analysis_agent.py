# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional
from azure.ai.projects.models import Agent
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ResponseFormatJsonSchema, ResponseFormatJsonSchemaType

from common.agent_factory.agent_base import AIFoundryAgentBase
from common.contracts.configuration.agent_config import AzureAIAgentConfig
from models.step_responses import PostCallAnalysis


class PostCallAnalysisAgent(AIFoundryAgentBase):
    """Agent for performing post-call analysis."""

    @classmethod
    def _is_singleton(cls) -> bool:
        return True

    async def _create_foundry_agent(self, configuration: AzureAIAgentConfig, project_client: AIProjectClient) -> Agent:
        """Create the post-call analysis agent in AI Foundry."""
        return await super()._create_foundry_agent(
            configuration=configuration,
            project_client=project_client,
            response_format=ResponseFormatJsonSchemaType(
                json_schema=ResponseFormatJsonSchema(
                    name="post_call_analysis",
                    description="Generate post call analysis for advisor and customer conversation.",
                    schema=PostCallAnalysis.model_json_schema(),
                )
            ),
        )
