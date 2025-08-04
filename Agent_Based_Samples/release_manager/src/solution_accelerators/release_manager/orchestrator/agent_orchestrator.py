# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
import json
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from agents.agent_factory import AgentFactory
from azure.ai.projects import AIProjectClient
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from models.agents import Agent
from models.devops_settings import DevOpsSettings
from models.jira_settings import JiraSettings
from models.visualization_settings import VisualizationSettings
from semantic_kernel import Kernel
from semantic_kernel.agents import (
    AgentResponseItem,
    AgentThread,
    AzureAIAgent,
    AzureAIAgentThread,
    ChatHistoryAgentThread,
)
from semantic_kernel.connectors.ai import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import AzureChatPromptExecutionSettings
from semantic_kernel.contents import (
    AuthorRole,
    ChatHistory,
    ChatMessageContent,
    FileReferenceContent,
    TextContent,
)
from semantic_kernel.functions import KernelArguments
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore
from utilities.blob_store_helper import BlobStoreHelper

from common.agent_factory.agent_base import AIFoundryAgentBase, SemanticKernelAgentBase
from common.contracts.common.answer import Answer
from common.contracts.configuration.orchestrator_config import (
    ResolvedOrchestratorConfig,
)
from common.contracts.orchestrator.request import Request
from common.contracts.orchestrator.response import Response
from common.sk_service.service_configurator import get_service
from common.telemetry.app_logger import AppLogger
from common.utilities.redis_message_handler import RedisMessageHandler

LOCAL_VISUALIZATION_DATA_DIR = "visualization"
KERNEL_AZURE_CHAT_COMPLETION_SERVICE_ID = "kernel_completion_service"

# Initialize the update messages to be displayed to the user
update_messages = [
    "Aggregating relevant information for your request...",
    "Compiling data for your query...",
    "Generating plan to provide accurate results...",
]

@dataclass
class AgentRuntimeConfig:
    agent: Union[SemanticKernelAgentBase, AIFoundryAgentBase]
    agent_thread: Union[ChatHistoryAgentThread, AzureAIAgentThread]


class AgentOrchestrator:
    def __init__(
        self,
        logger: AppLogger,
        message_handler: RedisMessageHandler,
        jira_settings: JiraSettings,
        devops_settings: DevOpsSettings,
        visualization_settings: VisualizationSettings,
        configuration: ResolvedOrchestratorConfig = None,
    ) -> None:
        self.logger = logger
        self.message_handler = message_handler

        self.jira_settings = jira_settings
        self.devops_settings = devops_settings

        self.blob_store_helper = BlobStoreHelper(visualization_settings.storage_account_name)
        self.blob_container = visualization_settings.visualization_data_blob_container

        # Semantic Kernel Settings
        self.kernel: Kernel = None
        self.project_client: AIProjectClient = None
        self.memory: SemanticTextMemory = None
        self.chat_history: ChatHistory = ChatHistory()

        # Agent threads
        self.planner_agent_thread: AzureAIAgentThread = None
        self.jira_agent_thread: ChatHistoryAgentThread = None
        self.devops_agent_thread: ChatHistoryAgentThread = None
        self.visualization_agent_thread: AzureAIAgentThread = None

        # Currently, configuration is updated only once per session i.e. for consecutive requests from the same session, configuration is not updated.
        # This is to avoid re-initializing the kernel and agents for every request.
        self.config: ResolvedOrchestratorConfig = configuration

        # Initialize agent name to agent instance map
        self.agent_runtime_config_map: Dict[Agent, AgentRuntimeConfig] = {}

    def __get_or_create_kernel(self) -> Kernel:
        """
        Create a kernel instance with Azure ChatCompletion service.

        Returns:
        Kernel: Kernel instance with Azure ChatCompletion service and base settings.
        """
        if self.kernel:
            return self.kernel

        self.kernel = Kernel()

        settings = AzureChatPromptExecutionSettings()
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto() # auto-invoke functions when available

        if self.config and self.config.service_configs:
            for service_config in self.config.service_configs:
                service_config = service_config.config_body
                self.logger.info(f"Adding service to kernel: {service_config.service_id}")
                self.kernel.add_service(get_service(service_config))
        else:
            raise ValueError("No service configurations found.")

        # Set up memory store
        embeddings_gen = self.kernel.get_service(service_id="embeddings_gen")
        if not embeddings_gen:
            self.logger.warning("Embeddings generator service not found in the kernel. Agent memory will be disabled.")
        else:
            self.memory = SemanticTextMemory(storage=VolatileMemoryStore(), embeddings_generator=embeddings_gen)

        return self.kernel

    async def __initialize_agent_threads(self, thread_id: str) -> None:
        # Retrieve the thread from Azure AI Foundry
        self.logger.info(f"Retrieving thread {thread_id} from AI Foundry..")
        request_thread: AgentThread = await self.project_client.agents.get_thread(thread_id)
        self.logger.info(f"Thread {request_thread.id} retrieved successfully from Azure AI Foundry!")

        # Initialize agent threads
        self.planner_agent_thread = AzureAIAgentThread(client=self.project_client, thread_id=request_thread.id)
        self.jira_agent_thread = ChatHistoryAgentThread(chat_history=self.chat_history)
        self.devops_agent_thread = ChatHistoryAgentThread(chat_history=self.chat_history)
        self.visualization_agent_thread = AzureAIAgentThread(client=self.project_client, thread_id=request_thread.id)
        self.fallback_agent_thread = ChatHistoryAgentThread(chat_history=self.chat_history)

    async def __invoke_agent(
        self,
        agent: Agent,
        messages: str | ChatMessageContent | list[str | ChatMessageContent],
        kernel_arguments: Optional[KernelArguments] = None,
    ) -> AgentResponseItem[ChatMessageContent]:
        """
        Invoke the specified agent with the provided messages and thread.
        """
        self.logger.info(f"Invoking agent of type: {agent}")

        agent_runtime_config = self.config.get_agent_config(agent.value)
        response = await self.agent_runtime_config_map.get(agent).agent.invoke_with_runtime_config(
            kernel=self.kernel,
            messages=messages,
            thread=self.agent_runtime_config_map.get(agent).agent_thread,
            runtime_config=agent_runtime_config,
            arguments=kernel_arguments,
        )

        if response is None:
            self.logger.warning(f"Agent {agent.name} response is empty.")

        return response

    async def __create_agent(
        self,
        agent: Agent,
        agent_thread: Union[ChatHistoryAgentThread, AzureAIAgentThread],
    ) -> AgentRuntimeConfig:
        agent_config = self.config.get_agent_config(agent.value)
        if not agent_config:
            raise ValueError(f"Agent {agent.value} configuration not found in the provided config.")

        _agent = None
        if agent == Agent.PLANNER_AGENT:
            _agent = await self.agent_factory.create_planner_agent(
                kernel=self.kernel,
                configuration=agent_config
            )
        elif agent == Agent.JIRA_AGENT:
            _agent = await self.agent_factory.create_jira_agent(
                kernel=self.kernel,
                configuration=agent_config,
                jira_settings=self.jira_settings
            )
        elif agent == Agent.DEVOPS_AGENT:
            _agent = await self.agent_factory.create_devops_agent(
                kernel=self.kernel,
                configuration=agent_config,
                devops_settings=self.devops_settings
            )
        elif agent == Agent.VISUALIZATION_AGENT:
            _agent = await self.agent_factory.get_visualization_agent(
                kernel=self.kernel,
                configuration=agent_config,
            )
        elif agent == Agent.FALLBACK_AGENT:
            _agent = await self.agent_factory.create_fallback_agent(
                kernel=self.kernel,
                configuration=agent_config,
            )
        else:
            raise ValueError(f"Unsupported agent type: {agent}")

        return AgentRuntimeConfig(agent=_agent, agent_thread=agent_thread)


    async def initialize_agent_workflow(self, thread_id: str) -> None:
        """
        Initialize the agent workflow by setting up the kernel, agents, and threads.
        """
        self.logger.info("Initializing agent workflow...")

        # KERNEL SETUP
        self.kernel = self.__get_or_create_kernel()

        # AZURE AI FOUNDRY SETUP
        self.project_client = AzureAIAgent.create_client(credential=DefaultAzureCredential())

        # THREADS SETUP
        await self.__initialize_agent_threads(thread_id)

        # AGENTS SETUP
        self.agent_factory: AgentFactory = await AgentFactory.get_instance()
        await self.agent_factory.initialize(self.logger, self.project_client, self.memory)

        # 1. PLANNER AGENT SETUP
        self.agent_runtime_config_map[Agent.PLANNER_AGENT] = await self.__create_agent(
            agent=Agent.PLANNER_AGENT,
            agent_thread=self.planner_agent_thread
        )

        # 2. JIRA AGENT SETUP
        self.agent_runtime_config_map[Agent.JIRA_AGENT] = await self.__create_agent(
            agent=Agent.JIRA_AGENT,
            agent_thread=self.jira_agent_thread
        )

        # 3. DEVOPS AGENT SETUP
        self.agent_runtime_config_map[Agent.DEVOPS_AGENT] = await self.__create_agent(
            agent=Agent.DEVOPS_AGENT,
            agent_thread=self.devops_agent_thread
        )

        # 4. VISUALIZATION AGENT SETUP
        self.agent_runtime_config_map[Agent.VISUALIZATION_AGENT] = await self.__create_agent(
            agent=Agent.VISUALIZATION_AGENT,
            agent_thread=self.visualization_agent_thread
        )

        # FALLBACK AGENT SETUP
        self.agent_runtime_config_map[Agent.FALLBACK_AGENT] = await self.__create_agent(
            agent=Agent.FALLBACK_AGENT,
            agent_thread=self.fallback_agent_thread,
        )

    async def __parse_planner_agent_response(self, planner_agent_response: AgentResponseItem[ChatMessageContent]) -> Dict[str, Any]:
        """
        Parse the planner agent response to extract the plan.
        """
        try:
            response_dict = json.loads(planner_agent_response.content.content)

            return {
                "plan_id": response_dict.get("plan_id"),
                "agents": response_dict.get("agents", []),
                "justification": response_dict.get("justification", "").strip()
            }
        except json.JSONDecodeError as e:
            self.logger.exception(f"Failed to parse planner agent response as JSON: {e}")
            raise ValueError("Invalid JSON response from planner agent.")

    async def __execute_planner(
        self,
        session_id: str,
        dialog_id: str,
        user_query: str,
        messages: str | ChatMessageContent | list[str | ChatMessageContent],
        kernel_arguments: KernelArguments
    ) -> Dict[str, Any]:
        """
        Execute the planner agent with the provided messages.
        """
        self.logger.info("Executing Planner Agent to generate orchestration plan...")

        # Add memory context if available. Only search for high relevance memory records.
        memory_context = await self.agent_runtime_config_map[Agent.PLANNER_AGENT].agent.search_memory_in_collection(
            collection_name=Agent.PLANNER_AGENT.value,
            query=user_query,
            max_result_count=3,
            min_relevance_score=0.7
        )

        # Update kernel arguments with memory context if available
        if memory_context:
            memory_context_str = "\n".join([record.text for record in memory_context])
            kernel_arguments["memory_context"] = memory_context_str

        planner_agent_response = await self.__invoke_agent(
            agent=Agent.PLANNER_AGENT,
            messages=messages,
            kernel_arguments=kernel_arguments,
        )

        parsed_response = await self.__parse_planner_agent_response(planner_agent_response)

        # Push memory hydration task to background and return parsed response
        asyncio.create_task(self.__store_plan(session_id, dialog_id, user_query, parsed_response))
        return parsed_response

    async def __store_plan(
        self,
        session_id: str,
        dialog_id: str,
        user_query: str,
        generated_plan: Dict[str, Any]
    ) -> str:
        memory_record = f"""
                        User Query: {user_query}
                        Selected Plan: {generated_plan["plan_id"]}
                        Agents: {', '.join(generated_plan["agents"])}
                        Justification: {generated_plan["justification"]}
                        """

        # Add memory context if available
        await self.agent_runtime_config_map[Agent.PLANNER_AGENT].agent.store_memory_in_collection(
            collection=Agent.PLANNER_AGENT.value,
            id=f"{session_id}_{dialog_id}",
            text=memory_record,
            description="Planner Agent generated plan information for the user query.",
        )

        self.logger.info(f"Planner memory context stored successfully for session {session_id} and dialog {dialog_id}.")


    async def __generate_visualization_data(self, agent_response: AgentResponseItem[ChatMessageContent], dialog_id: str) -> List[str]:
        visualization_image_sas_urls = []

        if len(agent_response.items) > 0:
            await self.message_handler.send_update(update_message="Generating visualization data...", dialog_id=dialog_id)

        try:
            for item in agent_response.items:
                try:
                    if isinstance(item, FileReferenceContent) and item.file_id is not None:
                        self.logger.info(f"Image File ID: {item.file_id}")
                        file_name = f"{item.file_id}_image_file.png"

                        # Save the image file to the target directory
                        await self.project_client.agents.save_file(
                            file_id=item.file_id,
                            file_name=file_name,
                            target_dir=LOCAL_VISUALIZATION_DATA_DIR,
                        )

                        # Upload image file to storage and get the URL
                        if self.blob_container:
                            image_url = await self.blob_store_helper.upload_file_and_get_sas_url(
                                container_name=self.blob_container,
                                blob_name=file_name,
                                local_file_path=os.path.join(LOCAL_VISUALIZATION_DATA_DIR, file_name),
                            )
                            visualization_image_sas_urls.append(image_url)
                except Exception as e:
                    self.logger.exception(f"Error processing image file ID {item.file_id}: {e}. Skipping this file.")
                    continue # Continue to the next file if an error occurs

            self.logger.info(f"Visualization data generated successfully with {len(visualization_image_sas_urls)} image(s).")
            await self.message_handler.send_update(
                update_message="Successfully generated visualization data. Almost there..",
                dialog_id=dialog_id,
            )

        except Exception as e:
            self.logger.exception(f"Error generating visualization data: {e}. Skipping.")
            await self.message_handler.send_update(
                update_message="Error generating visualization data. Please try again later.",
                dialog_id=dialog_id,
            )

        return visualization_image_sas_urls


    async def start_agent_workflow(self, request: Request) -> Response:
        """
        Start the agent workflow by invoking the JIRA and DevOps agents, and generating visualization data.

        Args:
            request (Request): The request object containing user input and session information.

        Returns:
            Response: The response object containing the final answer and visualization data.
        """
        self.logger.info("Starting agent workflow orchestration...")

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
            self.chat_history.add_user_message(request.message)

            try:
                kernel_args = KernelArguments()

                # Execute Planner agent to generate the plan
                plan = await self.__execute_planner(
                    session_id=request.session_id,
                    dialog_id=request.dialog_id,
                    user_query=request.message,
                    messages=self.chat_history.messages,
                    kernel_arguments=kernel_args
                )

                if not plan or Agent.FALLBACK_AGENT.value in plan.get('agents'):
                    self.logger.error("No plan generated by the Planner agent or no agents found in the plan. Invoking fallback agent..")

                    fallback_response = await self.__invoke_agent(Agent.FALLBACK_AGENT, message, kernel_args)
                    return Response(
                        session_id=request.session_id,
                        dialog_id=request.dialog_id,
                        thread_id=request.thread_id,
                        user_id=request.user_id,
                        answer=Answer(answer_string=fallback_response.content.content, is_final=True, data_points=[], speaker_locale=request.locale),
                    )

                self.logger.info(f"Orchestration Plan generated successfully: {plan}")

                update_message = random.choice(update_messages)
                await self.message_handler.send_update(update_message, dialog_id=request.dialog_id)

                intermediate_context = ""
                visualization_image_sas_urls: list[str] = []

                # Iterate through the agents in the plan and invoke them
                for agent_name in plan['agents']:
                    agent = Agent(agent_name)
                    if agent not in self.agent_runtime_config_map:
                        raise ValueError(f"Agent {agent} not found in configuration.")

                    # Invoke the agent with the plan
                    agent_response = await self.__invoke_agent(
                        agent=agent,
                        messages=intermediate_context if intermediate_context else message,
                        kernel_arguments=kernel_args,
                    )
                    self.logger.info(f"Agent {agent.name} response: {agent_response}")

                    # Visualization Agent responds with visualization data in the form of file IDs
                    # If the agent is the Visualization Agent, handle the response accordingly.
                    if agent == Agent.VISUALIZATION_AGENT:
                        visualization_image_sas_urls = await self.__generate_visualization_data(agent_response, request.dialog_id)
                    else:
                        # Clean up the response to remove any unwanted characters
                        clean_agent_response = agent_response.content.content.replace("\n", "").replace("\r", "")

                        # Pass full clean context to next agent
                        intermediate_context += f"{clean_agent_response}\n\n"

                # Update the chat history with the final response
                self.chat_history.add_assistant_message(intermediate_context)

                return Response(
                    session_id=request.session_id,
                    dialog_id=request.dialog_id,
                    thread_id=request.thread_id,
                    user_id=request.user_id,
                    answer=Answer(
                        answer_string=intermediate_context,
                        is_final=True,
                        data_points=visualization_image_sas_urls if visualization_image_sas_urls else [],
                        speaker_locale=request.locale,
                    ),
                )
            except HttpResponseError as http_error:
                self.logger.exception(f"HTTP error during agent invocation: {http_error}")
                raise
            except Exception as e:
                self.logger.exception(f"Error during agent invocation: {e}")
                raise
        except Exception as e:
            self.logger.exception(f"Exception occurred while orchestrating agents: {e}")
            raise