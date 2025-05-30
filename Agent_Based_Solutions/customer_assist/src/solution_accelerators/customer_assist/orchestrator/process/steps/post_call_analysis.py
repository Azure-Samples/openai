# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.kernel import Kernel
from semantic_kernel.agents import AzureAIAgent
from semantic_kernel.processes.kernel_process.kernel_process_step_context import (
    KernelProcessStepContext,
)
from semantic_kernel.agents import AzureAIAgentThread, AgentResponseItem
from semantic_kernel.functions.kernel_function_decorator import kernel_function

from common.telemetry.app_logger import AppLogger
from common.telemetry.log_helper import CustomLogger
from models.process_enums import FunctionNames
from models.step_requests import ConsolidateInsightsRequest, PostCallAnalysisRequest
from agents.post_call_analysis_agent import PostCallAnalysisAgent
from models.events import StepCompletionEvent
from models.step_responses import PostCallAnalysis


class PostCallAnalysisState(KernelBaseModel):
    """State for the Post Call Analysis step."""

    # Define state variables for post call analysis
    post_call_analysis: PostCallAnalysis = None

    def __init__(self, post_call_analysis: PostCallAnalysis = None):
        super().__init__()
        self.post_call_analysis = post_call_analysis or PostCallAnalysis(
            summary="",
            next_steps=[],
        )


class PostCallAnalysisStep(KernelProcessStep[PostCallAnalysisState]):
    """Post Call Analysis step."""

    _logger: AppLogger = None
    _state: PostCallAnalysisState = None
    _post_call_analysis_agent: PostCallAnalysisAgent = None
    _agent_thread: AzureAIAgentThread = None
    _kernel: Kernel = None

    def create_default_state(self) -> PostCallAnalysisState:
        """Creates the default PostCallAnalysisState."""
        return PostCallAnalysisState()

    def _create_or_get_kernel(
        self,
        base_kernel: Kernel,
    ) -> Kernel:
        """Create or get the kernel instance."""
        if not self._kernel:
            self._kernel = Kernel(services=base_kernel.services)
        return self._kernel

    def initialize(
        self,
        logger: AppLogger,
        agent_thread: AzureAIAgentThread,
        post_call_analysis_agent: PostCallAnalysisAgent,
        kernel: Kernel,
    ) -> None:
        """Initialize the PostCallAnalysisStep with required parameters."""
        self._logger = logger
        self._agent_thread = agent_thread
        self._post_call_analysis_agent = post_call_analysis_agent
        self._kernel = self._create_or_get_kernel(kernel)
        self._logger.info("PostCallAnalysisStep initialized successfully")

    async def activate(self, state: KernelProcessStepState[PostCallAnalysisState]):
        """Activates the step and sets the state."""
        try:
            state.state = state.state or self.create_default_state()
            self._state = state.state
            if not self._logger:
                self._logger = AppLogger(custom_logger=CustomLogger())
            self._logger.info("PostCallAnalysisStep activated successfully")
        except Exception as ex:
            self._logger.error(f"Error during activation of PostCallAnalysisStep: {str(ex)}")
            raise RuntimeError("Failed to activate PostCallAnalysisStep.") from ex

    async def _generate_user_prompt(self, request: PostCallAnalysisRequest) -> dict:
        """Generate the user prompt for the post-call analysis agent."""
        try:
            self._logger.info("Generating user prompt for post-call analysis")
            # Serialize the full request objects
            chat_history_dict = request.chat_history.to_dict() if request.chat_history else None
            completed_form_dict = request.completed_form.get_fields() if request.completed_form else None
            sentiment_analysis_dict = (
                request.sentiment_analysis.model_dump_json() if request.sentiment_analysis else None
            )

            user_prompt = {
                "chat_history": chat_history_dict,
                "completed_form": completed_form_dict,
                "sentiment_analysis": sentiment_analysis_dict,
            }

            self._logger.debug(f"User prompt generated: {user_prompt}")
            return user_prompt
        except Exception as ex:
            self._logger.error(f"Error while generating user prompt: {str(ex)}")
            raise RuntimeError("Failed to generate user prompt for post-call analysis.") from ex

    async def _generate_post_call_analysis(
        self,
        user_prompt: str,
    ) -> PostCallAnalysis:
        """Get the insights from the conversation."""
        try:
            self._logger.info("Generating post-call analysis")
            post_call_analysis_response: AgentResponseItem = (
                await self._post_call_analysis_agent.invoke_with_runtime_config(
                    messages=str(user_prompt), thread=self._agent_thread, kernel=self._kernel
                )
            )
            post_call_analysis = PostCallAnalysis.model_validate_json(str(post_call_analysis_response.content.content))
            self._logger.debug(f"Post Call Analysis response: {post_call_analysis}")

            return post_call_analysis
        except Exception as ex:
            self._logger.error(f"Error while fetching insights: {str(ex)}")
            raise RuntimeError("Failed to fetch insights from the post call analysis agent.") from ex

    @kernel_function(name=FunctionNames.POST_CALL_ANALYSIS)
    async def post_call_analysis(
        self, context: KernelProcessStepContext, kernel: Kernel, request: PostCallAnalysisRequest
    ) -> None:
        """Execute the post call analysis step."""
        try:
            self._logger.info("Starting post-call analysis")

            if not request:
                self._logger.error("No request data provided for post-call analysis")
                raise ValueError("PostCallAnalysisRequest is required.")

            if request.completed_form:
                self._logger.info("Analyzing completed loan application form")

            if request.sentiment_analysis:
                self._logger.debug(f"Processing sentiment scores: {request.sentiment_analysis}")

            # Simulate agent invocation (replace with actual agent call)
            self._logger.info("Invoking post-call analysis agent")
            user_prompt = await self._generate_user_prompt(request)
            analysis_result = await self._generate_post_call_analysis(user_prompt)
            self._logger.debug(f"Agent analysis complete: {analysis_result}")

            # Update state with analysis result
            self._state.post_call_analysis = analysis_result
            self._logger.info("Post-call analysis state updated successfully")

            # Emit event after successful analysis
            await context.emit_event(
                StepCompletionEvent.POST_CALL_ANALYSIS_COMPLETED,
                data=ConsolidateInsightsRequest(post_call_analysis=analysis_result),
            )
            self._logger.info("Emitted post-call analysis completed event")
        except ValueError as ve:
            self._logger.error(f"Validation error during post-call analysis: {str(ve)}")
            raise
        except Exception as ex:
            self._logger.error(f"Unexpected error during post-call analysis: {str(ex)}")
            raise RuntimeError("Failed to execute post-call analysis.") from ex
