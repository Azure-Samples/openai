# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
from typing import Optional

from models.agents import Agent
from models.jira_settings import JiraSettings
from plugins.jira_plugin import JiraPlugin
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.kernel import KernelArguments
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.agent_factory.agent_base import SemanticKernelAgentBase
from common.contracts.configuration.agent_config import SKAgentConfig
from common.telemetry.app_logger import AppLogger


class JiraAgent(SemanticKernelAgentBase):
    """
    JiraAgent provides integration with JIRA systems for the Release Manager.
    This agent is designed to be instantiated per session rather than shared.
    """

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        """Initialize the JiraAgent instance."""
        super().__init__(logger, memory)

    @classmethod
    def _is_singleton(cls) -> bool:
        """
        JiraAgent is not a singleton by default since it requires specific
        JIRA connection credentials that may vary by user/session.

        Returns:
            bool: False, indicating a new instance per session
        """
        return False

    async def _create_sk_agent(self, configuration: SKAgentConfig, **kwargs) -> ChatCompletionAgent:
        """
        Create a Semantic Kernel ChatCompletionAgent for JIRA integration.

        Args:
            configuration: Agent configuration
            jira_server_url: JIRA server URL
            jira_server_username: JIRA server username
            jira_server_password: JIRA server password
            **kwargs: Additional arguments for agent creation

        Returns:
            ChatCompletionAgent: The initialized JIRA agent
        """
        try:
            # Read JIRA instructions and field mapping from static files
            settings = JiraSettings(**kwargs)

            with open(os.path.join(settings.config_file_path, "jql_cheatsheet.md"), "r", encoding="utf-8") as f:
                jql_instructions = f.read()
            with open(os.path.join(settings.config_file_path, "jira_customfield_description.json"), "r", encoding="utf-8") as f:
                jira_customfield_description = f.read()

            # Create Jira plugin
            jira_plugin = JiraPlugin(
                logger=self._logger,
                settings=settings,
                memory=self._agent_memory,
                memory_store_collection_name=Agent.JIRA_AGENT.value,
                customfield_description_str=jira_customfield_description,
                jql_instructions=jql_instructions
            )
            await jira_plugin.initialize()

            # Add Jira plugin to kernel
            self._kernel.add_plugin(jira_plugin, plugin_name="JiraPlugin")

            # Prepare arguments if execution settings are available
            arguments = None
            if configuration.sk_prompt_execution_settings:
                arguments = KernelArguments(settings=configuration.sk_prompt_execution_settings)

            # Create Jira agent as a ChatCompletionAgent in SK
            jira_agent = ChatCompletionAgent(
                kernel=self._kernel,
                name=configuration.agent_name,
                arguments=arguments,
                instructions=configuration.prompt,
                description=configuration.description,
            )

            return jira_agent
        except Exception as ex:
            self._logger.error(f"Error creating Jira agent: {ex}")
            return None
