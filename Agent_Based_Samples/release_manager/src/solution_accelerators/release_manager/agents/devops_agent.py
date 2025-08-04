# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
from typing import Optional

from models.agents import Agent
from models.devops_settings import DevOpsSettings
from plugins.devops_plugin import DevOpsPlugin
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.kernel import KernelArguments
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.agent_factory.agent_base import SemanticKernelAgentBase
from common.contracts.configuration.agent_config import SKAgentConfig
from common.telemetry.app_logger import AppLogger


class DevOpsAgent(SemanticKernelAgentBase):
    """
    DevOpsAgent provides integration with DevOps system for the Release Manager.
    This agent is designed to be instantiated per session rather than shared across instances.
    """
    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        """Initialize the DevOpsAgent instance."""
        super().__init__(logger, memory)

    @classmethod
    def _is_singleton(cls) -> bool:
        """
        DevOpsAgent is not a singleton by default since it requires specific
        DevOps System connection credentials that may vary by user/session.

        Returns:
            bool: False, indicating a new instance per session
        """
        return False

    async def _create_sk_agent(self, configuration: SKAgentConfig, **kwargs) -> ChatCompletionAgent:
        """
        Create a Semantic Kernel ChatCompletionAgent for DevOps Agent.

        Args:
            configuration: Agent configuration
            **kwargs: Additional arguments for agent creation

        Returns:
            ChatCompletionAgent: The initialized DevOps agent
        """
        try:
            settings = DevOpsSettings(**kwargs)

            column_metadata = ""
            with open(os.path.join(settings.config_file_path, "devops_table_column_metadata.json"), "r", encoding="utf-8") as f:
                column_metadata = f.read()

            # Create DevOps plugin
            devops_plugin = DevOpsPlugin(
                logger=self._logger,
                devops_settings=settings,
                column_metadata_str=column_metadata,
                memory=self._agent_memory,
                memory_store_collection_name=Agent.DEVOPS_AGENT.value,
            )
            await devops_plugin.initialize()

            # Add DevOps plugin to kernel
            self._kernel.add_plugin(devops_plugin, plugin_name="DevOpsPlugin")

            # Prepare arguments if execution settings are available
            arguments = None
            if configuration.sk_prompt_execution_settings:
                arguments = KernelArguments(settings=configuration.sk_prompt_execution_settings)

            # Create DevOps agent as a ChatCompletionAgent in SK
            devops_agent = ChatCompletionAgent(
                kernel=self._kernel,
                name=configuration.agent_name,
                arguments=arguments,
                instructions=configuration.prompt,
                description=configuration.description,
            )

            return devops_agent
        except Exception as ex:
            self._logger.error(f"Error creating DevOps agent: {ex}")
            return None
