# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from semantic_kernel.kernel_pydantic import KernelBaseModel

from common.telemetry.app_logger import AppLogger

from semantic_kernel.processes.kernel_process.kernel_process_step import (
    KernelProcessStep,
)
from semantic_kernel.processes.kernel_process.kernel_process_step_context import (
    KernelProcessStepContext,
)
from semantic_kernel.processes.kernel_process.kernel_process_step_state import (
    KernelProcessStepState,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.functions.kernel_function_decorator import kernel_function

from common.telemetry.log_helper import CustomLogger
from models.process_enums import FunctionNames
from models.step_requests import ConsolidateInsightsRequest
from models.step_responses import AdvisorInsights, SentimentAnalysis, PostCallAnalysis, Sentiment, ConsolidatedInsights
from models.events import StepCompletionEvent


class InsightsState(KernelBaseModel):
    """State for the Consolidate Insights step."""

    consolidated_insights: ConsolidatedInsights = None

    def __init__(self, consolidated_insights: ConsolidatedInsights = None):
        super().__init__()
        self.consolidated_insights = consolidated_insights or ConsolidatedInsights(
            advisor_insights=AdvisorInsights(missing_fields=[], next_question=""),
            sentiment_analysis=SentimentAnalysis(sentiment=Sentiment.NEUTRAL.value),
            post_call_analysis=PostCallAnalysis(summary="", next_steps=[]),
            advisor_customer_chat_history=None,
        )


class ConsolidateInsightsStep(KernelProcessStep[InsightsState]):
    """Consolidate Insights step."""

    _logger: AppLogger = None
    _state: InsightsState = None

    def create_default_state(self) -> InsightsState:
        """Creates the default InsightsState."""
        return InsightsState()

    async def activate(self, state: KernelProcessStepState[InsightsState]):
        """Activates the step and sets the state."""
        try:
            if not self._logger:
                self._logger = AppLogger(custom_logger=CustomLogger())
            self._logger.info("Activating ConsolidateInsightsStep")
            state.state = state.state or self.create_default_state()
            self._state = state.state
            self._logger.debug("ConsolidateInsightsStep activated with state initialized")
        except Exception as ex:
            self._logger.error(f"Error during activation of ConsolidateInsightsStep: {str(ex)}")
            raise RuntimeError("Failed to activate ConsolidateInsightsStep.") from ex

    def initialize(self, logger: AppLogger) -> None:
        """Initialize the ConsolidateInsightsStep with required parameters."""
        self._logger = logger
        self._logger.info("ConsolidateInsightsStep initialized successfully")

    @kernel_function(name=FunctionNames.CONSOLIDATE_INSIGHTS)
    async def consolidate_insights(
        self, context: KernelProcessStepContext, request: ConsolidateInsightsRequest
    ) -> None:
        """Execute the consolidate insights step."""
        try:
            self._logger.info("Starting insights consolidation")
            self._logger.debug("Processing insights from multiple analysis")

            if not request:
                self._logger.error("No insights provided for consolidation")
                raise ValueError("Insights request is required for consolidation.")

            # Process advisor insights
            if request.advisor_insights:
                self._logger.debug(f"advisor insights: {request.advisor_insights.get_fields()}")
                self._state.consolidated_insights.advisor_insights = request.advisor_insights

            # Process advisor-customer chat history
            if request.advisor_customer_chat_history:
                self._logger.debug(f"advisor-customer chat history: {request.advisor_customer_chat_history}")
                self._state.consolidated_insights.advisor_customer_chat_history = request.advisor_customer_chat_history

            # Process sentiment analysis
            if request.sentiment_analysis:
                self._logger.debug(f"Sentiment analysis: {request.sentiment_analysis.sentiment}")
                self._state.consolidated_insights.sentiment_analysis = request.sentiment_analysis

            # Process post-call analysis
            if request.post_call_analysis:
                self._logger.debug(f"Post-call analysis: {request.post_call_analysis.summary}")
                self._state.consolidated_insights.post_call_analysis = request.post_call_analysis

            # Process form data
            if request.form_data:
                self._logger.debug(f"Form data: {request.form_data}")
                self._state.consolidated_insights.form_data = request.form_data

            # Emit event after successful consolidation
            await context.emit_event(StepCompletionEvent.INSIGHTS_CONSOLIDATED)
            self._logger.info("Emitted insights consolidated event")
        except ValueError as ve:
            self._logger.error(f"Validation error during insights consolidation: {str(ve)}")
        except Exception as ex:
            self._logger.error(f"Unexpected error during insights consolidation: {str(ex)}")
            raise RuntimeError("Failed to consolidate insights.") from ex
