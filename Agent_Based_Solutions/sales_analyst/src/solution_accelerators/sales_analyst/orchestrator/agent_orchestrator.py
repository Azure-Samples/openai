# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from common.telemetry.app_logger import AppLogger
from common.utilities.redis_message_handler import RedisMessageHandler
from common.contracts.orchestrator.request import Request
from common.contracts.orchestrator.response import Response
from common.contracts.configuration.orchestrator_config import ResolvedOrchestratorConfig
from semantic_kernel.agents import AzureAIAgent
from azure.identity import DefaultAzureCredential, OnBehalfOfCredential
from azure.ai.projects import AIProjectClient
from agents.agent_factory import AgentFactory
from semantic_kernel import Kernel
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentThread, AgentResponseItem
from semantic_kernel.contents import (
    AuthorRole,
    ChatHistory,
    ChatMessageContent,
    FileReferenceContent,
    AnnotationContent,
    TextContent,
)
from common.agent_factory.agent_base import AIFoundryAgentBase
from azure.core.exceptions import HttpResponseError
from common.contracts.common.answer import Answer
from config.default_config import DefaultConfig
from models.error import InvalidConsentError
from common.utilities.blob_store_helper import BlobStoreHelper
from typing import Any, Dict, List, Optional, Union
from models.visualization_settings import VisualizationSettings
import os
from urllib.parse import urlparse, parse_qs
from databricks.sdk import WorkspaceClient
from azure.core.exceptions import ClientAuthenticationError
import json
from plugins.databricks_plugin import DatabricksPlugin

LOCAL_VISUALIZATION_DATA_DIR = "visualization"
DATABRICKS_AUDIENCE_SCOPE = (
    "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default"  # Well know Databricks audience scope in Entra ID
)


class AgentOrchestrator:
    def __init__(
        self,
        logger: AppLogger,
        message_handler: RedisMessageHandler,
        configuration: ResolvedOrchestratorConfig,
        visualization_settings: VisualizationSettings,
    ) -> None:
        self.logger = logger
        self.message_handler = message_handler
        self.configuration = configuration

        self.blob_store_helper = BlobStoreHelper(
            logger=logger,
            storage_account_name=visualization_settings.storage_account_name,
            container_name=visualization_settings.visualization_data_blob_container,
        )
        self.blob_container = visualization_settings.visualization_data_blob_container

        self.project_client: AIProjectClient = None
        self.agent: AIFoundryAgentBase = None
        self.thread: AzureAIAgentThread = None
        self.databricks_client: WorkspaceClient = None
        self.obo_credential = None
        self.genie_space_id = None

        self.kernel = Kernel()

    async def initialize_agent(self, thread_id: str, user_token: str) -> None:
        """
        Initializes the agent for a given thread ID. Sets up Databricks workspace client.
        Args:
            thread_id (str): The unique identifier for the thread.
        """
        self.logger.info(f"Initializing agent for thread ID: {thread_id}")

        self.project_client = AzureAIAgent.create_client(
            credential=DefaultAzureCredential(), endpoint=DefaultConfig.AZURE_AI_AGENT_ENDPOINT
        )

        await self._initialize_databricks_client(
            connection_name=DefaultConfig.AZURE_AI_DATABRICKS_CONNECTION_NAME, user_token=user_token
        )

        self.thread = AzureAIAgentThread(client=self.project_client, thread_id=thread_id)

        agent_factory: AgentFactory = await AgentFactory.get_instance()
        await agent_factory.initialize(self.logger, self.project_client)

        self.kernel = Kernel()
        databricks_plugin = DatabricksPlugin(workspace_client=self.databricks_client, space_id=self.genie_space_id)
        self.kernel.add_plugin(databricks_plugin)

        self.agent = await agent_factory.get_sales_analyst_agent(
            kernel=self.kernel,
            configuration=self.configuration.get_agent_config("SALES_ANALYST_AGENT"),
        )

    async def run_agent(self, request: Request) -> Response:
        self.logger.info("Starting agent orchestration...")

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

        try:
            message = ChatMessageContent(role=AuthorRole.USER, items=[TextContent(text=request.message)])
            agent_runtime_config = self.configuration.get_agent_config("SALES_ANALYST_AGENT")

            await self.message_handler.send_update(
                update_message="Processing your request with the agent...",
                dialog_id=request.dialog_id,
            )

            response = await self.agent.invoke_with_runtime_config(
                kernel=self.kernel, messages=message, thread=self.thread, runtime_config=agent_runtime_config
            )

            if response is None:
                self.logger.warning(f"Agent response is empty.")

            bing_grounding_metadata = await self._get_bing_grounding_metadata(
                agent_response=response,
                dialog_id=request.dialog_id,
                thread_id=request.thread_id,
                run_id=response.metadata.get("run_id", ""),
            )

            visualization_image_sas_urls = await self.__generate_visualization_data(response, request.dialog_id)

            return Response(
                session_id=request.session_id,
                dialog_id=request.dialog_id,
                thread_id=request.thread_id,
                user_id=request.user_id,
                answer=Answer(
                    answer_string=response.content.content,
                    is_final=True,
                    data_points=visualization_image_sas_urls if visualization_image_sas_urls else [],
                    speaker_locale=request.locale,
                    additional_metadata={
                        "bing_grounding_metadata": bing_grounding_metadata,
                    },
                ),
            )

        except HttpResponseError as http_error:
            self.logger.exception(f"HTTP error during agent invocation: {http_error}")
            raise
        except Exception as e:
            self.logger.exception(f"Error during agent invocation: {e}")
            raise

    async def _initialize_databricks_client(self, connection_name: str, user_token: str) -> None:
        """
        Initializes the Databricks client using the provided connection name.
        Args:
            connection_name (str): The name of the Databricks connection.
        """
        self.logger.info(f"Initializing Databricks client with connection: {connection_name}")

        obo = OnBehalfOfCredential(
            tenant_id=DefaultConfig.TENANT_ID,
            client_id=DefaultConfig.CLIENT_ID,
            client_secret=DefaultConfig.CLIENT_SECRET,
            user_assertion=user_token,
        )

        try:
            token = obo.get_token(DATABRICKS_AUDIENCE_SCOPE)
        except ClientAuthenticationError as ex:
            err = json.loads(ex.response.internal_response.text)["error"]
            sub = json.loads(ex.response.internal_response.text)["suberror"]
            if err == "invalid_grant" and sub == "consent_required":
                raise InvalidConsentError(f"Failed to obtain token for Databricks client: {err}, suberror: {sub}")

        try:
            databricks_connection = await self.project_client.connections.get(connection_name)
            self.genie_space_id = databricks_connection.metadata["genie_space_id"]
            self.databricks_client = WorkspaceClient(
                host=databricks_connection.target,
                token=token.token,
            )
            self.logger.info("Databricks client initialized successfully.")
        except Exception as e:
            self.logger.exception(f"Failed to initialize Databricks client: {e}")
            raise

    async def _get_bing_grounding_metadata(
        self, agent_response: AgentResponseItem[ChatMessageContent], dialog_id: str, thread_id: str, run_id: str
    ) -> Dict[str, Any]:
        bing_search_annotations = []
        bing_search_queries = []

        # send update if there are Bing Grounding annotations
        if any(isinstance(item, AnnotationContent) for item in agent_response.items):
            await self.message_handler.send_update(
                update_message="Processing Bing Grounding results...",
                dialog_id=dialog_id,
            )

        # Fetch Bing Grounding annotations from the agent response

        try:
            for item in agent_response.items:
                if isinstance(item, AnnotationContent):
                    if (
                        item.url
                    ):  # Hack to identify Bing Grounding annotations (File References are also returned as AnnotationContent)
                        bing_search_annotations.append(
                            {
                                "quote": item.quote,
                                "title": item.title,
                                "url": item.url,
                            }
                        )

            # Fetch run steps to get Bing Grounding details to get search queries

            run_steps = self.project_client.agents.run_steps.list(thread_id=thread_id, run_id=run_id)
            async for step in run_steps:
                step_details = step.get("step_details", {})
                tool_calls = step_details.get("tool_calls", [])

                if tool_calls:
                    for call in tool_calls:
                        bing_grounding_details = call.get("bing_grounding", {})
                        if bing_grounding_details:
                            # Extract the 'q' parameter from the Bing search URL
                            request_url = bing_grounding_details.get("requesturl", "")
                            parsed_url = urlparse(request_url)
                            query_params = parse_qs(parsed_url.query)
                            query = query_params.get("q", [""])[0]
                            bing_search_queries.append(query)

        except Exception as e:
            self.logger.exception(f"Error parsing Bing Grounding data: {e}. Skipping.")

        return {
            "bing_search_queries": bing_search_queries,
            "bing_search_annotations": bing_search_annotations,
        }

    async def __generate_visualization_data(
        self, agent_response: AgentResponseItem[ChatMessageContent], dialog_id: str
    ) -> List[str]:
        visualization_image_sas_urls = []  # check each item in the agent response for FileReferenceContent
        if any(isinstance(item, FileReferenceContent) for item in agent_response.items):
            await self.message_handler.send_update(
                update_message="Generating visualization data...",
                dialog_id=dialog_id,
            )

        try:
            for item in agent_response.items:
                try:
                    if isinstance(item, FileReferenceContent) and item.file_id is not None:
                        self.logger.info(f"Image File ID: {item.file_id}")
                        file_name = f"{item.file_id}_image_file.png"

                        # Save the image file to the target directory
                        await self.project_client.agents.files.save(
                            file_id=item.file_id,
                            file_name=file_name,
                            target_dir=LOCAL_VISUALIZATION_DATA_DIR,
                        )

                        # Upload image file to storage and get the URL
                        if self.blob_container:
                            # Read the file content and upload using common helper
                            local_file_path = os.path.join(LOCAL_VISUALIZATION_DATA_DIR, file_name)
                            with open(local_file_path, "rb") as file_data:
                                file_content = file_data.read()

                            # Upload the file content
                            blob_client = self.blob_store_helper.container_client.get_blob_client(file_name)
                            await blob_client.upload_blob(file_content, overwrite=True)

                            # Generate SAS URL
                            image_url = await self.blob_store_helper.generate_blob_sas_url(blob_name=file_name)
                            visualization_image_sas_urls.append(image_url)
                except Exception as e:
                    self.logger.exception(f"Error processing image file ID {item.file_id}: {e}. Skipping this file.")
                    continue  # Continue to the next file if an error occurs

            self.logger.info(
                f"Visualization data generated successfully with {len(visualization_image_sas_urls)} image(s)."
            )

        except Exception as e:
            self.logger.exception(f"Error generating visualization data: {e}. Skipping.")

        return visualization_image_sas_urls
