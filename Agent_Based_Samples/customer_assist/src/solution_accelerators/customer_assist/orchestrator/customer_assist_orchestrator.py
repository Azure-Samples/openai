# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai import FunctionChoiceBehavior

from common.contracts.configuration.orchestrator_config import ResolvedOrchestratorConfig
from common.contracts.orchestrator.request import Request
from common.contracts.orchestrator.response import Response
from common.sk_service.service_configurator import get_service

from common.telemetry.app_logger import AppLogger
from process.assist_process import CustomerAssistProcess
from models.content_understanding_settings import ContentUnderstandingSettings


class ProcessOrchestrator:
    _kernel: Kernel = None

    def __init__(
        self,
        logger: AppLogger,
        configuration: ResolvedOrchestratorConfig = None,
        content_understanding_settings: ContentUnderstandingSettings = None,
    ):
        self.logger = logger
        self.configuration = configuration
        self.assist_process: CustomerAssistProcess = None
        self.content_understanding_settings = content_understanding_settings

    def get_or_create_kernel(self) -> Kernel:
        """
        Create a kernel instance with Azure ChatCompletion service.

        Returns:
        Kernel: Kernel instance with Azure ChatCompletion service and base settings.
        """
        if self._kernel:
            return self._kernel

        try:
            self._kernel = Kernel()

            # Setup kernel settings to auto-invoke functions when available.
            settings = AzureChatPromptExecutionSettings()
            settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

            if self.configuration and self.configuration.service_configs:
                for service_config in self.configuration.service_configs:
                    service_config = service_config.config_body
                    self.logger.info(f"Adding service to kernel: {service_config.service_id}")
                    self._kernel.add_service(get_service(service_config))
            else:
                raise ValueError("No service configurations found.")
            return self._kernel
        except Exception as e:
            self.logger.error(f"Failed to create or configure kernel: {str(e)}")
            raise RuntimeError("Kernel initialization failed.") from e

    async def initialize_process(self, request: Request):
        """
        Initialize the process with the given request.

        Args:
            request (Request): The request object containing process details.

        Raises:
            RuntimeError: If process initialization fails.
        """
        try:
            self.logger.set_base_properties(
                {
                    "ApplicationName": "ORCHESTRATOR_SERVICE",
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "thread_id": request.thread_id,
                    "dialog_id": request.dialog_id,
                }
            )
            self.logger.info("Received agent workflow orchestration request.")

            # Initialize the process
            self._kernel = self.get_or_create_kernel()
            self.logger.info("Kernel created successfully.")
            self.logger.info("Initializing process with request.")

            customer_profile = None
            if request and request.additional_metadata:
                self.logger.info(f"Request additional properties: {request.additional_metadata}")
                customer_profile = request.additional_metadata.get("customer_profile")

            self.assist_process = CustomerAssistProcess(
                logger=self.logger,
                config=self.configuration,
                kernel=self._kernel,
                content_understanding_settings=self.content_understanding_settings,
                customer_profile=customer_profile,
            )
            self.logger.info("Process initialized successfully.")
            process = await self.assist_process.create_process()
            if not process:
                self.logger.error("Failed to create process.")
                raise RuntimeError("Failed to create process.")
        except ValueError as ve:
            self.logger.error(f"Invalid configuration during process initialization: {str(ve)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during process initialization: {str(e)}")
            raise RuntimeError("Process initialization failed.") from e

    async def run_process(self, request: Request) -> Response:
        """
        Start the process with the given request.

        Args:
            request (Request): The request object containing process details.

        Returns:
            Response: The response object after running the process.

        Raises:
            RuntimeError: If the process fails to run.
        """
        try:
            self.logger.set_base_properties(
                {
                    "ApplicationName": "ORCHESTRATOR_SERVICE",
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "thread_id": request.thread_id,
                    "dialog_id": request.dialog_id,
                }
            )
            self.logger.info("Starting process with request.")

            # Start the process
            if not self.assist_process:
                await self.initialize_process(request)

            response = await self.assist_process.run_process(request=request)
            self.logger.info(f"Process run successfully with response: {response}")
            return response
        except RuntimeError as re:
            self.logger.error(f"Process runtime error: {str(re)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during process execution: {str(e)}")
            raise RuntimeError("Process execution failed.") from e
