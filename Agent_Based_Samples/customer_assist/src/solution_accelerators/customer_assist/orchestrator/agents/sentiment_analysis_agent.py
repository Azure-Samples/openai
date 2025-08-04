# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional
from azure.ai.projects.models import Agent
from azure.ai.projects import AIProjectClient
from semantic_kernel import Kernel
from common.agent_factory.agent_base import AIFoundryAgentBase, SemanticKernelAgentBase
from common.contracts.configuration.agent_config import AzureAIAgentConfig
from azure.ai.projects.models import ResponseFormatJsonSchema, ResponseFormatJsonSchemaType
from models.step_responses import SentimentAnalysis


class SentimentAnalysisAgent(AIFoundryAgentBase):
    """Agent for analyzing sentiment in conversations."""

    @classmethod
    def _is_singleton(cls) -> bool:
        return True

    async def _create_foundry_agent(self, configuration: AzureAIAgentConfig, project_client: AIProjectClient) -> Agent:
        """Create the sentiment analysis agent in AI Foundry."""
        return await super()._create_foundry_agent(
            configuration=configuration,
            project_client=project_client,
            response_format=ResponseFormatJsonSchemaType(
                json_schema=ResponseFormatJsonSchema(
                    name="sentiment_analysis",
                    description="Sentiment analysis for conversations.",
                    schema=SentimentAnalysis.model_json_schema(),
                )
            ),
        )


class LocalSentimentAnalysisAgent(SemanticKernelAgentBase):
    """Agent for analyzing sentiment in conversations using AzureAIInference."""

    @classmethod
    def _is_singleton(cls) -> bool:
        return False
