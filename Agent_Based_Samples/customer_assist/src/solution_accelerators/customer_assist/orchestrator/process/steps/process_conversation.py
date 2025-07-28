# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from typing import List
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep
from semantic_kernel.processes.kernel_process.kernel_process_step_state import KernelProcessStepState
from semantic_kernel.kernel import Kernel
from semantic_kernel.agents import AzureAIAgentThread, AgentResponseItem
from semantic_kernel.processes.kernel_process.kernel_process_step_context import KernelProcessStepContext
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from common.contracts.common.user_profile import UserRole
from common.contracts.configuration.agent_config import AzureAIAgentConfig
from common.contracts.orchestrator.request import Request
from common.telemetry.app_logger import AppLogger
from common.telemetry.log_helper import CustomLogger
from agents.plugins.form_completion import FormPlugin
from models.events import StepCompletionEvent, StepTriggerEvent
from models.step_requests import (
    AdvisorCustomerChatHistory,
    ConsolidateInsightsRequest,
    ProcessConversationRequest,
    SentimentAnalysisRequest,
)
from models.process_enums import FunctionNames
from agents.process_conversation_agent import AssistantAgent
from models.step_responses import AdvisorInsights
from models.content_understanding_settings import (
    ContentUnderstandingSettings,
)
from agents.plugins.content_understanding import ContentUnderstandingPlugin
from semantic_kernel.contents import AuthorRole, ChatMessageContent, FileReferenceContent, ImageContent, TextContent


class ConversationState(KernelBaseModel):
    """State for the Process Conversation step."""

    advisor_insights: AdvisorInsights = None
    advisor_customer_chat_history: AdvisorCustomerChatHistory = None

    def __init__(self, advisor_insights: AdvisorInsights = None):
        super().__init__()
        self.advisor_insights = advisor_insights or AdvisorInsights(
            missing_fields=[],
            next_question="",
        )
        self.advisor_customer_chat_history = AdvisorCustomerChatHistory(dialogs=[])


class ProcessConversationStep(KernelProcessStep[ConversationState]):
    """Process Conversation step for analyzing call transcripts."""

    _logger: AppLogger = None
    _state: ConversationState = None
    _assistant_agent: AssistantAgent = None
    _agent_thread: AzureAIAgentThread = None
    _agent_config: AzureAIAgentConfig = None
    _kernel: Kernel = None

    PROCESS_TRANSCRIPT_USER_PROMPT: str = f"""
        <EXISTING_CUSTOMER_INFORMATION_IN_SYSTEM>
        {{existing_customer_information}}
        <EXISTING_CUSTOMER_INFORMATION_IN_SYSTEM>

        <CURRENT_FORM_STATE>
        {{current_form_state}}
        <CURRENT_FORM_STATE>

        <advisor_CUSTOMER_CONVERSATION>
        {{advisor_customer_history}}
        <advisor_CUSTOMER_CONVERSATION>
    """

    def initialize(
        self,
        logger: AppLogger,
        agent_config: AzureAIAgentConfig,
        assistant_agent: AssistantAgent,
        agent_thread: AzureAIAgentThread,
        kernel: Kernel = None,
        # Content understanding configuration
        content_understanding_settings: ContentUnderstandingSettings = None,
    ):
        self._agent_config = agent_config
        self._assistant_agent = assistant_agent
        self._logger = logger
        self._agent_thread = agent_thread
        self._agent_thread = agent_thread
        self._logger.info("ProcessConversationStep initialized with agent configuration")
        self._kernel = self._create_or_get_kernel(
            kernel, content_understanding_settings=content_understanding_settings
        )

    def create_default_state(self) -> ConversationState:
        """Creates the default ConversationState."""
        return ConversationState()

    async def activate(self, state: KernelProcessStepState[ConversationState]):
        """Activates the step and sets the state."""
        try:
            state.state = state.state or self.create_default_state()
            self._state = state.state
            if not self._logger:
                self._logger = AppLogger(custom_logger=CustomLogger())
            self._logger.info("ProcessConversationStep activated successfully")
            if not self._assistant_agent:
                self._logger.error("Assistant agent is not initialized")
                raise RuntimeError("Assistant agent is not initialized")
        except Exception as ex:
            self._logger.error(f"Error during activation of ProcessConversationStep: {str(ex)}")
            raise RuntimeError("Failed to activate ProcessConversationStep.") from ex

    async def _get_user_prompt(self, request: ProcessConversationRequest) -> ChatMessageContent:
        """Get the user prompt for the conversation processing."""
        self._logger.debug("Generating user prompt for conversation processing")
        self._state.advisor_customer_chat_history.append_advisor_customer_dialog(request.advisor_customer_dialog)

        text_content = TextContent(
            text=self.PROCESS_TRANSCRIPT_USER_PROMPT.format(
                existing_customer_information=request.customer_profile,
                current_form_state=self._form_completion_plugin.form.get_fields(),
                advisor_customer_history=json.dumps(self._state.advisor_customer_chat_history.to_dict(), indent=2),
            )
        )
        items = [text_content]
        self._logger.debug(f"Text content created: {text_content}")
        chat_message_content = ChatMessageContent(
            role=AuthorRole.USER,
            items=items,
        )
        return chat_message_content

    async def _get_insights(self, user_prompt, image=None) -> AdvisorInsights:
        """Get the insights from the conversation."""
        try:
            self._logger.info("Fetching insights from the assistant agent")

            advisor_insights_response: AgentResponseItem = await self._assistant_agent.invoke_with_runtime_config(
                messages=user_prompt, thread=self._agent_thread, kernel=self._kernel
            )
            advisor_insights = AdvisorInsights.model_validate_json(str(advisor_insights_response.content.content))
            self._logger.debug(f"Insights received: {advisor_insights}")

            return advisor_insights
        except Exception as ex:
            self._logger.error(f"Error while fetching insights: {str(ex)}")
            raise RuntimeError("Failed to fetch insights from the assistant agent.") from ex

    def _create_or_get_kernel(
        self,
        base_kernel: Kernel,
        content_understanding_settings: ContentUnderstandingSettings = None,
    ) -> Kernel:
        """Create or get the kernel instance."""
        if not self._kernel:
            self._kernel = Kernel(services=base_kernel.services)
            # Create the form completion plugin the first time the kernel is created
            # i.e. the first time the step function is called
            self._form_completion_plugin = FormPlugin(logger=self._logger)
            self._kernel.add_plugin(
                self._form_completion_plugin,
                plugin_name="FormPlugin",
                description="Plugin to help with loan form completion",
            )

            if not content_understanding_settings:
                self._logger.error("Content understanding settings are required")
                raise ValueError("Content understanding settings are required.")

            self._content_understanding_plugin = ContentUnderstandingPlugin(
                logger=self._logger,
                content_understanding_settings=content_understanding_settings,
            )

            self._kernel.add_plugin(
                self._content_understanding_plugin,
                plugin_name="ContentUnderstandingPlugin",
                description="Plugin to help with document verification for the loan application",
            )

            self._logger.info("Kernel instance created and form completion plugin initialized")
        return self._kernel

    @kernel_function(name=FunctionNames.PROCESS_CONVERSATION)
    async def process_conversation(
        self, kernel: Kernel, context: KernelProcessStepContext, request: ProcessConversationRequest
    ) -> None:
        """Execute the conversation processing step."""
        try:
            self._logger.info("Starting conversation processing")
            self._logger.debug(f"Processing message from user role: {request.advisor_customer_dialog.user_role}")

            if not self._assistant_agent:
                self._logger.error("Assistant agent is not initialized")
                raise RuntimeError("Assistant agent is not initialized")

            if not request or not request.advisor_customer_dialog:
                self._logger.error("No request data provided for conversation processing")
                raise ValueError("ProcessConversationRequest is required.")

            if not self._kernel:
                self._kernel = self._create_or_get_kernel(kernel)

            # Process conversation using agent
            self._logger.info("Invoking conversation processing agent")
            user_prompt = await self._get_user_prompt(request)
            self._logger.debug(f"User prompt for conversation processing: {user_prompt}")
            
            advisor_insights = await self._get_insights(user_prompt=user_prompt)
            self._logger.debug(f"advisor insights received: {advisor_insights}")
            self._logger.info("Conversation processing state updated successfully")

            # Emit event after successful processing
            await context.emit_event(
                StepCompletionEvent.CONVERSATION_PROCESSED,
                data=ConsolidateInsightsRequest(
                    advisor_insights=advisor_insights,
                    advisor_customer_chat_history=self._state.advisor_customer_chat_history,
                    form_data=self._form_completion_plugin.form,
                ),
            )

            # For advisor dialog, emit the event for sentiment analysis
            if request.advisor_customer_dialog.user_role == UserRole.CUSTOMER:
                await context.emit_event(
                    StepTriggerEvent.ANALYZE_SENTIMENT,
                    data=SentimentAnalysisRequest(
                        advisor_customer_chat_history=self._state.advisor_customer_chat_history,
                    ),
                )
                self._logger.info("Emitted sentiment analysis event")
            self._logger.info("Emitted conversation processed event")

        except ValueError as ve:
            self._logger.error(f"Validation error during conversation processing: {str(ve)}")
            raise
        except RuntimeError as re:
            self._logger.error(f"Runtime error during conversation processing: {str(re)}")
            raise
        except Exception as ex:
            self._logger.error(f"Unexpected error during conversation processing: {str(ex)}")
            raise RuntimeError("Failed to process conversation.") from ex
