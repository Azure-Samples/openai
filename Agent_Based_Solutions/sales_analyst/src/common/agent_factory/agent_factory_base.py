# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
from typing import Union

from azure.ai.projects import AIProjectClient
from semantic_kernel import Kernel
from semantic_kernel.agents import Agent as SKAgent

from common.agent_factory.agent_base import AIFoundryAgentBase, SemanticKernelAgentBase
from common.contracts.configuration.agent_config import (
    AzureAIAgentConfig,
    ChatCompletionAgentConfig,
)
from common.telemetry.app_logger import AppLogger


class AgentFactory:
    def __init__(self, logger: AppLogger, client: AIProjectClient):
        if not client:
            raise ValueError("AIProjectClient cannot be None.")
        self.client = client
        self.logger = logger

    async def create_agent(
        self,
        configuration: Union[AzureAIAgentConfig, ChatCompletionAgentConfig],
        kernel: Kernel | None = None
    ) -> SKAgent:
        """
        Create an SK agent based on the provided configuration.
        """
        if isinstance(configuration, AzureAIAgentConfig):
            agent_base = await AIFoundryAgentBase.get_instance()
            return await agent_base.initialize(kernel=kernel, configuration=configuration, logger=self.logger, client=self.client)
        elif isinstance(configuration, ChatCompletionAgentConfig):
            agent_base = await SemanticKernelAgentBase.get_instance()
            return await agent_base.initialize(kernel=kernel, configuration=configuration, logger=self.logger)
        else:
            raise ValueError("Unsupported agent configuration type.")
