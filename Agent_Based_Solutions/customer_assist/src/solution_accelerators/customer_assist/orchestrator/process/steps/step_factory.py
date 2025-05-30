# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Dict, Optional
from semantic_kernel.kernel import Kernel
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.agents import AzureAIAgentThread, ChatHistoryAgentThread
from azure.ai.projects import AIProjectClient

from common.contracts.configuration.orchestrator_config import ResolvedOrchestratorConfig
from models.process_enums import StepNames, AgentNames
from agents.agent_factory import AgentFactory
from common.telemetry.app_logger import AppLogger
from models.content_understanding_settings import ContentUnderstandingSettings
from agents.sentiment_analysis_agent import SentimentAnalysisAgent
from process.steps.consolidate_insights import ConsolidateInsightsStep
from process.steps.post_call_analysis import PostCallAnalysisStep
from process.steps.sentiment_analysis import SentimentAnalysisStep
from process.steps.process_conversation import ProcessConversationStep


class StepFactory:
    """Factory responsible for creating and managing lifecycle of proccess steps."""

    def __init__(
        self,
        logger: AppLogger,
        kernel: Kernel,
        agent_factory: AgentFactory,
        configuration: ResolvedOrchestratorConfig,
        client: AIProjectClient,
        content_understanding_settings: ContentUnderstandingSettings,
    ):
        self._logger = logger
        self._kernel = kernel
        self._agent_factory = agent_factory
        self._steps: Dict[StepNames, KernelProcessStep] = {}
        self._configuration: ResolvedOrchestratorConfig = configuration
        self._client: AIProjectClient = client
        self._content_understanding_settings: ContentUnderstandingSettings = content_understanding_settings

    async def _create_thread(self, thread_id: str = None):
        try:
            if thread_id:
                self._logger.debug(f"Creating agent thread with ID: {thread_id}")
                return AzureAIAgentThread(thread_id=thread_id)
            self._logger.debug("Creating a new agent thread")
            agent_thread = await self._client.agents.create_thread()
            if not agent_thread:
                self._logger.error("Failed to create agent thread")
                raise RuntimeError("Failed to create agent thread")
            agent_thread_id = agent_thread.id
            return AzureAIAgentThread(client=self._client, thread_id=agent_thread_id)
        except Exception as e:
            self._logger.error(f"Failed to create agent thread: {str(e)}")
            raise RuntimeError(f"Error creating agent thread: {str(e)}")

    # ProcessFramework requires step instances to be created without constructor parameters, throws errors.
    # The agent and thread configuration must be set after instantiation through property
    # assignment due to framework initialization constraints.

    async def create_conversation_step(self) -> KernelProcessStep:
        """Create the conversation step with the assistant agent."""
        if StepNames.PROCESS_CONVERSATION not in self._steps:
            self._logger.info("Creating conversation step")
            agent_config = self._configuration.get_agent_config(AgentNames.ASSIST_AGENT.value)
            if not agent_config:
                self._logger.error("Assistant agent configuration not found")
                raise ValueError("Assistant agent configuration is required")
            agent = await self._agent_factory.get_assistant_agent(kernel=self._kernel, configuration=agent_config)
            agent_thread = await self._create_thread()
            self._logger.debug(f"Creating agent thread: {agent_thread.id}")
            step_instance = ProcessConversationStep()
            step_instance.initialize(
                logger=self._logger,
                agent_config=agent_config,
                assistant_agent=agent,
                agent_thread=agent_thread,
                kernel=self._kernel,
                content_understanding_settings=self._content_understanding_settings,
            )
            step_instance._logger = self._logger
            step_instance._assistant_agent = agent
            step_instance._agent_thread = agent_thread
            self._steps[StepNames.PROCESS_CONVERSATION] = step_instance
        return self._steps[StepNames.PROCESS_CONVERSATION]

    async def create_sentiment_step(self) -> KernelProcessStep:
        if StepNames.SENTIMENT_ANALYSIS not in self._steps:
            agent_config = self._configuration.get_agent_config(AgentNames.SENTIMENT_ANALYSIS_AGENT.value)
            if not agent_config:
                self._logger.error("Sentiment analysis agent configuration not found")
                raise ValueError("Sentiment analysis agent configuration is required")
            agent = await self._agent_factory.get_sentiment_agent(
                kernel=self._kernel,
                configuration=agent_config,
            )
            if isinstance(agent, SentimentAnalysisAgent):
                agent_thread = await self._create_thread()
            else:
                agent_thread = ChatHistoryAgentThread()
            step_instance = SentimentAnalysisStep()
            self._logger.debug(f"Created agent thread for sentiment analysis: {agent_thread.id}")
            step_instance.initialize(
                logger=self._logger,
                agent_thread=agent_thread,
                sentiment_agent=agent,
                kernel=self._kernel,
                configuration=agent_config,
            )
            self._steps[StepNames.SENTIMENT_ANALYSIS] = step_instance
        return self._steps[StepNames.SENTIMENT_ANALYSIS]

    async def create_post_call_step(self) -> KernelProcessStep:
        if StepNames.POST_CALL_ANALYSIS not in self._steps:
            self._logger.info("Creating Post Call Analysis step")
            agent_config = self._configuration.get_agent_config(AgentNames.POST_CALL_ANALYSIS_AGENT.value)
            if not agent_config:
                self._logger.error("Post call analysis agent configuration not found")
                raise ValueError("Post call analysis agent configuration is required")
            agent = await self._agent_factory.get_post_call_agent(
                kernel=self._kernel,
                configuration=agent_config,
            )
            agent_thread = await self._create_thread()
            self._logger.debug(f"Created agent thread for post call analysis: {agent_thread.id}")
            step_instance = PostCallAnalysisStep()
            step_instance.initialize(
                logger=self._logger,
                agent_thread=agent_thread,
                post_call_analysis_agent=agent,
                kernel=self._kernel,
            )

            self._logger.debug(f"Creating agent thread: {agent_thread.id}")
            self._steps[StepNames.POST_CALL_ANALYSIS] = step_instance
        return self._steps[StepNames.POST_CALL_ANALYSIS]

    def create_consolidate_insights_step(self) -> KernelProcessStep:
        # ConsolidateInsightsStep does not require an agent, so we can create it directly.
        if StepNames.CONSOLIDATE_INSIGHTS not in self._steps:
            step_instance = ConsolidateInsightsStep()
            step_instance.initialize(logger=self._logger)
            self._logger.debug("Creating ConsolidateInsightsStep")
            self._steps[StepNames.CONSOLIDATE_INSIGHTS] = step_instance
        return self._steps[StepNames.CONSOLIDATE_INSIGHTS]
