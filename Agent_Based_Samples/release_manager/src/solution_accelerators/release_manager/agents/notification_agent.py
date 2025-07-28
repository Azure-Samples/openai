# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
from string import Template
from typing import Optional

from plugins.notification_plugin import NotificationPlugin
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.kernel import KernelArguments
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.agent_factory.agent_base import SemanticKernelAgentBase
from common.contracts.configuration.agent_config import SKAgentConfig
from common.telemetry.app_logger import AppLogger


class NotificationAgent(SemanticKernelAgentBase):
    """
    NotificationAgent provides integration with Microsoft Graph for sending notifications.
    This agent is designed to be instantiated per session rather than shared.
    """

    def __init__(self, logger: AppLogger, memory: Optional[SemanticTextMemory] = None):
        """Initialize the NotificationAgent instance."""
        super().__init__(logger, memory)

    @classmethod
    def _is_singleton(cls) -> bool:
        """
        NotificationAgent is not a singleton by default since it requires specific
        Microsoft Graph configuration that may vary by user/session.

        Returns:
            bool: False, indicating a new instance per session
        """
        return False

    async def _create_sk_agent(self, configuration: SKAgentConfig, **kwargs) -> ChatCompletionAgent:
        """
        Create a Semantic Kernel ChatCompletionAgent for Notifications.

        Args:
            configuration: Agent configuration
            sender_email: Sender email address
            receiver_email: Receiver email address
            email_template: Email template for the notification
            tenant_id: Azure AD tenant ID
            client_id: Azure AD application (client) ID
            managed_identity_client_id: Managed Identity client ID for authentication

        Returns:
            ChatCompletionAgent: The initialized Notification agent
        """
        try:
            # Read static Email template file
            email_template: Template = None
            email_template_file_path = os.path.join(os.path.dirname(__file__), "../static", "notification_email_template.html")
            with open(email_template_file_path, "r", encoding="utf-8") as template_file:
                email_template = Template(template_file.read())

            # Create Notification plugin
            notification_plugin = NotificationPlugin(
                logger=self._logger,
                sender_email=kwargs.get("sender_email"),
                receiver_email=kwargs.get("receiver_email"),
                email_template=email_template,
                tenant_id=kwargs.get("tenant_id"),
                client_id=kwargs.get("client_id"),
                managed_identity_client_id=kwargs.get("managed_identity_client_id"),
            )

            # Add Notification plugin to kernel
            self._kernel.add_plugin(notification_plugin, plugin_name="NotificationPlugin")

            # Prepare arguments if execution settings are available
            arguments = None
            if configuration.sk_prompt_execution_settings:
                arguments = KernelArguments(settings=configuration.sk_prompt_execution_settings)

            # Create Notification agent as a ChatCompletionAgent in SK
            notification_agent = ChatCompletionAgent(
                kernel=self._kernel,
                name=configuration.agent_name,
                arguments=arguments,
                instructions=configuration.prompt,
                description=configuration.description,
            )

            return notification_agent
        except Exception as ex:
            self._logger.error(f"Error creating Notification agent: {ex}")
            return None
