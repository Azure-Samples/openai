# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional

from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.kernel import KernelArguments
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.agent_factory.agent_base import SemanticKernelAgentBase
from common.contracts.configuration.agent_config import SKAgentConfig
from common.telemetry.app_logger import AppLogger


class FallbackAgent(SemanticKernelAgentBase):
    """
    FallbackAgent provides fallback option when planner fails to generate a plan.
    This agent is designed to be instantiated per session rather than shared.
    """

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        """Initialize the FallbackAgent instance."""
        super().__init__(logger, memory)

    @classmethod
    def _is_singleton(cls) -> bool:
        """
        FallbackAgent is not a singleton by default.

        Returns:
            bool: False, indicating a new instance per session
        """
        return False

    async def _create_sk_agent(
        self,
        configuration: SKAgentConfig,
        **kwargs,
    ) -> ChatCompletionAgent:
        """
        Create a Semantic Kernel ChatCompletionAgent for Fallback conversation.

        Args:
            configuration: Agent configuration
            **kwargs: Additional arguments for agent creation

        Returns:
            ChatCompletionAgent: The initialized Fallback agent
        """
        try:
            # Prepare arguments if execution settings are available
            arguments = None
            if configuration.sk_prompt_execution_settings:
                arguments = KernelArguments(settings=configuration.sk_prompt_execution_settings)

            # Create Fallback agent as a ChatCompletionAgent in SK
            fallback_agent = ChatCompletionAgent(
                kernel=self._kernel,
                name=configuration.agent_name,
                arguments=arguments,
                instructions=configuration.prompt,
                description=configuration.description,
            )

            return fallback_agent
        except Exception as ex:
            self._logger.error(f"Error creating Fallback agent: {ex}")
            return None
