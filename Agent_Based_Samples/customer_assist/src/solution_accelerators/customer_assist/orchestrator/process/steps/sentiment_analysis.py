# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from typing import List
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_step_state import (
    KernelProcessStepState,
)
from semantic_kernel.processes.kernel_process.kernel_process_step import (
    KernelProcessStep,
)
from semantic_kernel.processes.kernel_process.kernel_process_step_context import (
    KernelProcessStepContext,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.agents import AzureAIAgentThread, AgentResponseItem, ChatHistoryAgentThread
from semantic_kernel.functions.kernel_function_decorator import kernel_function

from common.contracts.configuration.agent_config import AzureAIAgentConfig, ChatCompletionAgentConfig
from common.telemetry.app_logger import AppLogger
from common.telemetry.log_helper import CustomLogger
from models.process_enums import FunctionNames
from models.step_requests import AdvisorCustomerDialog, ConsolidateInsightsRequest, SentimentAnalysisRequest
from models.events import StepCompletionEvent
from agents.sentiment_analysis_agent import LocalSentimentAnalysisAgent, SentimentAnalysisAgent
from models.step_responses import (
    Sentiment,
    SentimentAnalysis,
)


class SentimentAnalysisState(KernelBaseModel):
    """State for the Sentiment Analysis step."""

    sentiment_analysis: SentimentAnalysis = None

    def __init__(self, sentiment_analysis: SentimentAnalysis = None):
        super().__init__()
        self.sentiment_analysis = sentiment_analysis or SentimentAnalysis(
            sentiment=Sentiment.NEUTRAL.value, reasoning="Neutral"
        )


class SentimentAnalysisStep(KernelProcessStep[SentimentAnalysisState]):
    """Sentiment Analysis step."""

    _logger: AppLogger = None
    _state: SentimentAnalysisState = None
    _sentiment_agent: SentimentAnalysisAgent | LocalSentimentAnalysisAgent = None
    _configuration: AzureAIAgentConfig | ChatCompletionAgentConfig = None
    _agent_thread: AzureAIAgentThread = None
    _kernel: Kernel = None

    SENTIMENT_ANALYSIS_USER_PROMPT: str = f"""
        Here is the updated advisor-customer conversation history:
        <ADVISOR_CUSTOMER_CONVERSATION>
        {{advisor_customer_history}}
        <ADVISOR_CUSTOMER_CONVERSATION>
    """

    def create_default_state(self) -> SentimentAnalysisState:
        """Creates the default SentimentAnalysisState."""
        return SentimentAnalysisState()

    def initialize(
        self,
        logger: AppLogger,
        agent_thread: AzureAIAgentThread | ChatHistoryAgentThread,
        sentiment_agent: SentimentAnalysisAgent,
        kernel: Kernel,
        configuration: AzureAIAgentConfig | ChatCompletionAgentConfig,
    ) -> None:
        """Initialize the SentimentAnalysisStep with required parameters."""
        self._logger = logger
        self._agent_thread = agent_thread
        self._sentiment_agent = sentiment_agent
        self._kernel = self._create_or_get_kernel(kernel)
        self._configuration = configuration
        self._logger.info("SentimentAnalysisStep initialized successfully")

    async def activate(self, state: KernelProcessStepState[SentimentAnalysisState]):
        """Activates the step and sets the state."""
        try:
            if not self._logger:
                self._logger = AppLogger(custom_logger=CustomLogger())

            self._logger.info("Activating SentimentAnalysisStep")
            state.state = state.state or self.create_default_state()
            self._state = state.state
            self._logger.debug("SentimentAnalysisStep activated with state initialized")
        except Exception as ex:
            self._logger.error(f"Error during activation of SentimentAnalysisStep: {str(ex)}")
            raise RuntimeError("Failed to activate SentimentAnalysisStep.") from ex

    def _create_or_get_kernel(self, base_kernel: Kernel) -> Kernel:
        """Create or get the kernel instance."""
        if not self._kernel:
            self._kernel = Kernel(services=base_kernel.services)
            # TODO: Create the escalation plugin and add it to the kernel
            self._logger.info("Kernel instance created and form completion plugin initialized")
        return self._kernel

    def _get_user_prompt(self, advisor_customer_history: List[AdvisorCustomerDialog]) -> str:
        """Get the user prompt for sentiment analysis."""
        return self.SENTIMENT_ANALYSIS_USER_PROMPT.format(advisor_customer_history=advisor_customer_history)

    def _parse_sentiment_analysis_response(self, response: str) -> SentimentAnalysis:
        """Parse the sentiment analysis response."""
        try:
            return SentimentAnalysis.model_validate_json(response)
        except Exception as ex:
            # This is a fallback to handle cases where the response is not in the expected format.
            # LocalSentimentAnalysis agent uses Azure AI Inference API currently which returns a string
            # that needs to be parsed.
            # Expected format for local sentiment analysis agent is:
            # ```json\n{\n  "sentiment": "Neutral",\n  "reasoning": "reasoning string."\n}\n```'
            try:
                if response.startswith("```json"):
                    response = response[7:-3]  # strip ```json and ```
                    cleaned_response = response.encode("utf-8").decode("unicode_escape")
                    parsed_response = json.loads(cleaned_response)
                    return SentimentAnalysis(**parsed_response)
                else:
                    self._logger.error("Sentiment analysis response is not in JSON format")
                    raise ValueError("Sentiment analysis response is not in JSON format.")
            except json.JSONDecodeError as json_ex:
                self._logger.error(f"Failed to parse sentiment analysis response: {str(json_ex)}")
                raise RuntimeError("Failed to parse sentiment analysis response.") from json_ex
            except Exception as ex:
                self._logger.error(f"Failed to parse sentiment analysis response: {str(ex)}")
                raise RuntimeError("Failed to parse sentiment analysis response.") from ex

    async def _execute_sentiment_analysis(self, user_prompt: str) -> SentimentAnalysis:
        try:
            self._logger.info("Generating sentiment analysis")
            sentiment_analysis_response: AgentResponseItem = await self._sentiment_agent.invoke_with_runtime_config(
                messages=user_prompt,
                thread=self._agent_thread,
                kernel=self._kernel,
                runtime_config=self._configuration,
            )
            if not sentiment_analysis_response:
                self._logger.error("Sentiment analysis response is empty")
                raise RuntimeError("Sentiment analysis response is empty.")
            try:
                return self._parse_sentiment_analysis_response(str(sentiment_analysis_response.content.content))
            except Exception as ex:
                self._logger.debug(f"Failed to parse sentiment analysis response: {str(ex)}")
                sentiment_analysis = SentimentAnalysis(sentiment=Sentiment.NEUTRAL.value, reasoning="")

            self._logger.debug(f"Sentiment Analysis agent response: {sentiment_analysis}")

            return sentiment_analysis
        except Exception as ex:
            self._logger.error(f"Error while executing sentiment analysis: {str(ex)}")
            raise RuntimeError("Failed to perform sentiment analysis.") from ex

    @kernel_function(name=FunctionNames.SENTIMENT_ANALYSIS)
    async def sentiment_analysis(
        self, context: KernelProcessStepContext, kernel: Kernel, request: SentimentAnalysisRequest
    ) -> None:
        """Execute the sentiment analysis step."""
        try:
            self._logger.info("Starting sentiment analysis")
            self._logger.debug(f"Analyzing sentiment: {request.advisor_customer_chat_history}")

            if not request:
                self._logger.error("No request data provided for sentiment analysis")
                raise ValueError("SentimentAnalysisRequest is required.")

            if not self._sentiment_agent:
                self._logger.error("Sentiment analysis agent is not initialized")
                raise RuntimeError("Sentiment analysis agent is not initialized.")

            if not self._kernel:
                self._kernel = self._create_or_get_kernel(kernel)

            # Process using sentiment agent
            self._logger.info("Invoking sentiment analysis agent")

            user_prompt = self._get_user_prompt(request.advisor_customer_chat_history)
            self._logger.debug(f"User prompt for sentiment analysis: {user_prompt}")

            sentiment_analysis_result = await self._execute_sentiment_analysis(user_prompt)

            self._logger.debug(f"Sentiment analysis complete: {sentiment_analysis_result}")

            # Update state with analysis result
            self._state.sentiment_analysis = sentiment_analysis_result
            self._logger.info("Sentiment analysis state updated successfully")

            # Emit event after successful analysis
            await context.emit_event(
                StepCompletionEvent.SENTIMENT_ANALYZED,
                data=ConsolidateInsightsRequest(sentiment_analysis=sentiment_analysis_result),
            )
            self._logger.info("Emitted sentiment analyzed event")

        except ValueError as ve:
            self._logger.error(f"Validation error during sentiment analysis: {str(ve)}")
            raise
        except RuntimeError as re:
            self._logger.error(f"Runtime error during sentiment analysis: {str(re)}")
            raise
        except Exception as ex:
            self._logger.error(f"Unexpected error during sentiment analysis: {str(ex)}")
            raise RuntimeError("Failed to execute sentiment analysis.") from ex
