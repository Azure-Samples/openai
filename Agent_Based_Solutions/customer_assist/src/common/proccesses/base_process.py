# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from semantic_kernel.processes.process_builder import ProcessBuilder
from common.contracts.configuration.orchestrator_config import ResolvedOrchestratorConfig
from common.contracts.orchestrator.request import Request
from common.telemetry.app_logger import AppLogger
from semantic_kernel.processes.kernel_process.kernel_process import KernelProcess
from semantic_kernel.kernel import Kernel


class BaseProcess(ABC):
    """Base class for all processes in the system."""

    def __init__(self, logger: AppLogger, kernel: Kernel, config: ResolvedOrchestratorConfig = None):
        self.logger = logger
        self.config = config
        self.process: KernelProcess = None
        self.kernel: Kernel = kernel
        self.logger.info(f"Initialized {self.__class__.__name__}")
        if config:
            self.logger.debug(f"Process configured with: {config}")

    @abstractmethod
    def create_process(self, **kwargs: Any) -> ProcessBuilder:
        """
        Create and configure the process with steps.

        Returns:
            ProcessBuilder: Configured process builder instance
        """
        pass

    @abstractmethod
    async def run_process(self, **kwargs: Any) -> Any:
        """
        Execute the process.

        Args:
            request: The incoming request containing context and message
        Returns:
            Any: Process execution result
        """
        pass
