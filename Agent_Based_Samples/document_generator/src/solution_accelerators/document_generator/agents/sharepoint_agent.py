#  Copyright (c) Microsoft Corporation.
#  Licensed under the MIT license.

import os
import json
from typing import Optional

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import Connection
from azure.ai.agents.models import Agent as FoundryAgent
from azure.ai.agents.models import (
    ToolSet,
    SharepointTool,
    AgentThread,
    RunStatus,
)
from common.agent_factory.agent_base import AzureAIFoundryAgentBase
from common.contracts.configuration.agent_config import AIFoundryAgentConfig


class SharePointAgent(AzureAIFoundryAgentBase):

    @classmethod
    def _is_singleton(cls) -> bool:
        """
        Override to indicate this agent should use the singleton pattern.

        Returns:
            bool: True, indicating a singleton instance
        """
        return True

    async def _create_foundry_agent(
        self,
        configuration: AIFoundryAgentConfig,
        project_client: AIProjectClient,
        **kwargs,
    ) -> FoundryAgent:
        """
        Creates a SharePoint agent with the specified connection name.

        Args:
            sharepoint_connection_name (str): The name of the SharePoint connection to use.
        """
        if not kwargs.get("sharepoint_connection_name"):
            raise ValueError(
                "SharePoint connection name must be provided."
                "Either provide them explicitly or set the environment variable SHAREPOINT_CONNECTION_NAME."
            )

        try:
            sharepoint_connection_name = kwargs.get("sharepoint_connection_name") or os.getenv(
                "SHAREPOINT_CONNECTION_NAME"
            )
            self._logger.info(f"Getting SharePoint connection: {sharepoint_connection_name}")
            sharepoint_connection: Connection = await project_client.connections.get(
                sharepoint_connection_name, include_credentials=True
            )
        except Exception as e:
            self._logger.error(f"Error accessing connection: {str(e)}")
            raise ValueError(
                f"Failed to retrieve SharePoint connection '{sharepoint_connection_name}': {str(e)}"
            ) from e

        if not sharepoint_connection:
            raise ValueError(
                "Please provide a valid SharePoint connection name. "
                f"No connection found with name: {sharepoint_connection_name}"
            )

        toolset = ToolSet()
        toolset.add(SharepointTool(connection_id=sharepoint_connection.id))

        sharepoint_agent = await project_client.agents.create_agent(
            model=configuration.model,
            name=configuration.name,
            instructions=configuration.instructions,
            toolset=toolset,
        )

        return sharepoint_agent

    def _get_annotations(self, annotations):
        """
        Extracts and formats annotations from agent's message.

        Args:
            annotations (list): List of annotations from the agent's message.

        Returns:
            list: A list of formatted annotation dictionaries.
        """
        sharepoint_annotations = []
        for annotation in annotations:
            if annotation.type == "url_citation":
                sharepoint_annotations.append(
                    {
                        "url_citation": annotation.url_citation.url,
                    }
                )
        return sharepoint_annotations

    async def invoke_with_runtime_config(
        self,
        messages: str,
        thread: AgentThread,
        runtime_config: Optional[AIFoundryAgentConfig] = None,
        project_client: AIProjectClient = None,
        **kwargs,
    ):
        """
        Invoke the SharePoint agent with a user query.

        Args:
            agent_id (str): The ID of the SharePoint agent to invoke.
            thread_id (str): The ID of the thread to use for the invocation.
            query (str): User query to process
        """
        try:
            thread_id = thread.id
            agent_id = self._agent.id
            self._logger.info(f"Invoking SharePoint Agent with query: {messages}")
            message = await project_client.agents.messages.create(thread_id=thread_id, content=messages, role="user")

            run = await project_client.agents.runs.create_and_process(
                thread_id=thread_id,
                agent_id=agent_id,
                instructions=runtime_config.instructions if runtime_config else None,
                top_p=runtime_config.top_p if runtime_config else None,
                temperature=runtime_config.temperature if runtime_config else None,
                max_prompt_tokens=(runtime_config.max_prompt_tokens if runtime_config else None),
                max_completion_tokens=(runtime_config.max_completion_tokens if runtime_config else None),
            )

            # Check run status
            if run.status != RunStatus.COMPLETED:
                self._logger.error(f"SharePoint agent run failed with status: {run.status}")
                raise RuntimeError(f"SharePoint agent run failed with status: {run.status}")

            async for message in project_client.agents.messages.list(thread_id=thread_id):
                if message.text_messages and message.role.value == "assistant":
                    last_message = message.text_messages[-1].text
                    message_value = last_message.value
                    message_annotations = self._get_annotations(last_message.annotations)

                    # If annotations exist, add them to the message value
                    if message_annotations:
                        # Convert annotations to string and append to message
                        annotations_text = "\n\nSources:\n" + json.dumps(message_annotations, indent=2)
                        combined_message = message_value + annotations_text
                        return combined_message

                    return message_value

        except Exception as e:
            self._logger.error(f"Error invoking SharePoint agent: {str(e)}")
            raise e
