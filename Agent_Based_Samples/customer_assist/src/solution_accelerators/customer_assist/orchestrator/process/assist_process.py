# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
CustomerCallAssistProcess: Orchestrates the customer call assistance workflow using a modular, event-driven process.

This process coordinates conversation handling, sentiment analysis, post-call analysis, and insight consolidation steps.
"""

from typing import Any, Dict, Optional
from semantic_kernel import Kernel
from semantic_kernel.processes.process_builder import ProcessBuilder

from common.contracts.common.answer import Answer
from common.contracts.configuration.orchestrator_config import ResolvedOrchestratorConfig
from common.contracts.orchestrator.response import Response
from common.proccesses.base_process import BaseProcess
from common.contracts.orchestrator.request import Request
from common.telemetry.app_logger import AppLogger
from common.utilities.blob_store_helper import BlobStoreHelper
from models.step_responses import ConsolidatedInsights
from models.process_enums import FunctionNames, StepNames
from models.events import ProcessInputEvent, StepTriggerEvent, StepCompletionEvent
from models.step_requests import AdvisorCustomerDialog, PostCallAnalysisRequest, ProcessConversationRequest
from agents.agent_factory import AgentFactory
from models.content_understanding_settings import ContentUnderstandingSettings
from process.steps.consolidate_insights import ConsolidateInsightsStep, InsightsState
from process.steps.sentiment_analysis import SentimentAnalysisStep
from process.steps.post_call_analysis import PostCallAnalysisStep
from process.steps.step_factory import StepFactory
from process.steps.process_conversation import ProcessConversationStep
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.processes.local_runtime.local_kernel_process import start
from semantic_kernel.processes.kernel_process.kernel_process_event import KernelProcessEvent
from semantic_kernel.processes.kernel_process import KernelProcessStepState


class CustomerAssistProcess(BaseProcess):
    """
    Orchestrates the customer call assistance workflow, managing the lifecycle of conversation, sentiment analysis,
    post-call analysis, and insight consolidation steps. Utilizes a modular, event-driven process pipeline.
    """

    def __init__(
        self,
        logger: AppLogger,
        kernel: Kernel,
        config: Optional[ResolvedOrchestratorConfig] = None,
        content_understanding_settings: Optional[ContentUnderstandingSettings] = None,
        customer_profile: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the CustomerCallAssistProcess.

        Args:
            logger (AppLogger): Logger instance for telemetry.
            kernel (Kernel): Semantic kernel instance.
            config (ResolvedOrchestratorConfig, optional): Orchestrator configuration.
            content_understanding_settings (ContentUnderstandingSettings, optional): Content understanding settings.
            customer_profile (Dict[str, Any], optional): Customer profile data.
        """
        super().__init__(logger, kernel, config)
        self.logger.info("Initializing CustomerCallAssistProcess")
        self.process: Optional[KernelProcess] = None
        self._latest_insights: Optional[ConsolidatedInsights] = None
        self._content_understanding_settings: Optional[ContentUnderstandingSettings] = content_understanding_settings
        self._customer_profile: Dict[str, Any] = customer_profile or {}
        self._agent_factory: Optional[AgentFactory] = None
        self._step_factory: Optional[StepFactory] = None
        self.project_client: Any = None

    async def create_process(self) -> KernelProcess:
        """
        Create and configure the process pipeline with all required steps and event connections.

        Returns:
            KernelProcess: The constructed process pipeline.

        Raises:
            RuntimeError: If process creation fails.
        """
        try:
            self.logger.info("Starting process creation for CustomerCallAssist")
            self._agent_factory = await AgentFactory.get_instance()
            await self._agent_factory.__init_async__(self.logger)
            self.project_client = await self._agent_factory.initialize_project_client()
            self._step_factory = StepFactory(
                logger=self.logger,
                kernel=self.kernel,
                agent_factory=self._agent_factory,
                configuration=self.config,
                client=self.project_client,
                content_understanding_settings=self._content_understanding_settings,
            )

            self.logger.info("Building CustomerCallAssist process")
            process_builder = ProcessBuilder(name="CustomerCallAssistProcess")

            # Add steps to the process
            self.logger.info("Adding process conversation step")
            process_conversation_step = process_builder.add_step(
                step_type=ProcessConversationStep,
                name=StepNames.PROCESS_CONVERSATION.value,
                factory_function=self._step_factory.create_conversation_step,
            )
            self.logger.debug(f"Created step: {StepNames.PROCESS_CONVERSATION.value}")

            self.logger.info("Adding sentiment analysis step")
            sentiment_analysis_step = process_builder.add_step(
                step_type=SentimentAnalysisStep,
                name=StepNames.SENTIMENT_ANALYSIS.value,
                factory_function=self._step_factory.create_sentiment_step,
            )
            self.logger.debug(f"Created step: {StepNames.SENTIMENT_ANALYSIS.value}")

            self.logger.info("Adding post call analysis step")
            post_call_analysis_step = process_builder.add_step(
                step_type=PostCallAnalysisStep,
                name=StepNames.POST_CALL_ANALYSIS.value,
                factory_function=self._step_factory.create_post_call_step,
            )
            self.logger.debug(f"Created step: {StepNames.POST_CALL_ANALYSIS.value}")

            self.logger.info("Adding consolidate insights step")
            consolidate_insights_step = process_builder.add_step(
                step_type=ConsolidateInsightsStep,
                name=StepNames.CONSOLIDATE_INSIGHTS.value,
                factory_function=self._step_factory.create_consolidate_insights_step,
            )
            self.logger.debug(f"Created step: {StepNames.CONSOLIDATE_INSIGHTS.value}")

            # Add input events to the process
            process_builder.on_input_event(event_id=ProcessInputEvent.NEW_MESSAGE_RECEIVED).send_event_to(
                target=process_conversation_step,
                function_name=FunctionNames.PROCESS_CONVERSATION,
                parameter_name="request",
            )

            process_builder.on_input_event(event_id=ProcessInputEvent.CALL_ENDED).send_event_to(
                target=post_call_analysis_step,
                function_name=FunctionNames.POST_CALL_ANALYSIS,
                parameter_name="request",
            )

            # Connect the steps in the process
            process_conversation_step.on_event(event_id=StepTriggerEvent.ANALYZE_SENTIMENT).send_event_to(
                target=sentiment_analysis_step,
                function_name=FunctionNames.SENTIMENT_ANALYSIS,
                parameter_name="request",
            )

            process_conversation_step.on_event(event_id=StepCompletionEvent.CONVERSATION_PROCESSED).send_event_to(
                target=consolidate_insights_step,
                function_name=FunctionNames.CONSOLIDATE_INSIGHTS,
                parameter_name="request",
            )

            sentiment_analysis_step.on_event(event_id=StepCompletionEvent.SENTIMENT_ANALYZED).send_event_to(
                target=consolidate_insights_step,
                function_name=FunctionNames.CONSOLIDATE_INSIGHTS,
                parameter_name="request",
            )

            post_call_analysis_step.on_event(event_id=StepCompletionEvent.POST_CALL_ANALYSIS_COMPLETED).send_event_to(
                target=consolidate_insights_step,
                function_name=FunctionNames.CONSOLIDATE_INSIGHTS,
                parameter_name="request",
            )

            self.process = process_builder.build()
            self.logger.info("CustomerCallAssist process created successfully")
            return self.process
        except Exception as ex:
            self.logger.error(f"Error during process creation: {ex!r}")
            raise RuntimeError("Failed to create CustomerCallAssist process.") from ex

    async def run_process(self, request: Request, **kwargs: Any) -> Response:
        """
        Execute the process pipeline with the given request.

        Args:
            request (Request): The incoming request to process.
            **kwargs: Additional keyword arguments.

        Returns:
            Response: The orchestrated response containing insights or error details.

        Raises:
            ValueError: If the process is not created before execution.
        """
        try:
            self.logger.info("Starting CustomerCallAssist process execution")

            if not self.process:
                self.logger.error("Process not created before execution")
                raise ValueError("Process not created. Call create_process first.")

            self.logger.debug(f"Executing process with parameters: {request}")

            # Prepare the initial event and data for the process
            process_message_request: Optional[ProcessConversationRequest] = None
            initial_event: Optional[KernelProcessEvent] = None

            if request and request.additional_metadata and request.additional_metadata.get("end_of_call", False):
                self.logger.info("End of call detected, invoking post-call analysis")
                if not self._latest_insights:
                    self.logger.error("No latest insights available for post-call analysis.")
                    return Response(
                        session_id=request.session_id,
                        dialog_id=request.dialog_id,
                        user_id=request.user_id,
                        answer=Answer(is_final=False),
                        error="No insights available for post-call analysis.",
                    )
                # Prepare context for post-call analysis
                post_call_analysis_request = PostCallAnalysisRequest(
                    sentiment_analysis=self._latest_insights.sentiment_analysis,
                    advisor_insights=self._latest_insights.advisor_insights,
                    chat_history=self._latest_insights.advisor_customer_chat_history,
                    completed_form=self._latest_insights.form_data,
                )
                initial_event = KernelProcessEvent(
                    id=ProcessInputEvent.CALL_ENDED,
                    data=post_call_analysis_request,
                )
            else:
                # Prepare context for conversation processing
                process_message_request = ProcessConversationRequest(
                    customer_profile=self._customer_profile,
                    advisor_customer_dialog=AdvisorCustomerDialog(
                        message=request.message, user_role=request.user_profile.role
                    ),
                )
                initial_event = KernelProcessEvent(
                    id=ProcessInputEvent.NEW_MESSAGE_RECEIVED,
                    data=process_message_request,
                )

            # Run the process pipeline
            async with await start(
                process=self.process,
                kernel=self.kernel,
                data=process_message_request,
                initial_event=initial_event,
            ) as running_process:
                process_state = await running_process.get_state()
                self.logger.info("Process execution completed successfully")
                output_step_state: Optional[KernelProcessStepState[InsightsState]] = next(
                    (
                        s.state
                        for s in process_state.steps
                        if getattr(s.state, "name", None) == StepNames.CONSOLIDATE_INSIGHTS.value
                    ),
                    None,
                )

                if (
                    output_step_state
                    and getattr(output_step_state, "state", None)
                    and getattr(output_step_state.state, "consolidated_insights", None)
                ):
                    additional_metadata = {}
                    self._latest_insights = output_step_state.state.consolidated_insights
                    if self._latest_insights:
                        self.logger.info("Consolidated insights successfully retrieved")
                        additional_metadata = {
                            "insights": self._latest_insights.advisor_insights.model_dump_json(),
                            "sentiment_analysis": self._latest_insights.sentiment_analysis.model_dump_json(),
                            "post_call_analysis": self._latest_insights.post_call_analysis.model_dump_json(),
                            "form_data": self._latest_insights.form_data.model_dump_json(),
                        }
                    return Response(
                        session_id=request.session_id,
                        dialog_id=request.dialog_id,
                        user_id=request.user_id,
                        answer=Answer(
                            is_final=True,
                            additional_metadata=additional_metadata,
                        ),
                        error=None,
                    )
                else:
                    self.logger.error("Output step state not found or insights missing in process state")
                    return Response(
                        session_id=request.session_id,
                        dialog_id=request.dialog_id,
                        user_id=request.user_id,
                        answer=Answer(is_final=True),
                        error="Insights could not be consolidated",
                    )
        except ValueError as ve:
            self.logger.error(f"Validation error during process execution: {ve!r}")
            raise
        except Exception as ex:
            self.logger.error(f"Unexpected error during process execution: {ex!r}")
            return Response(
                session_id=getattr(request, "session_id", None),
                dialog_id=getattr(request, "dialog_id", None),
                user_id=getattr(request, "user_id", None),
                answer=Answer(is_final=True),
                error=str(ex),
            )
