# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, Union
from urllib.parse import parse_qs, urlparse

from agents.agent_factory import AgentFactory
from azure.ai.projects import AIProjectClient
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from models.agents import Agent
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
    AnnotationContent,
    AuthorRole,
    ChatHistory,
    ChatMessageContent,
    TextContent,
)
from semantic_kernel.functions import KernelArguments
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory
from semantic_kernel.memory.volatile_memory_store import VolatileMemoryStore

from common.agent_factory.agent_base import AzureAIAgentBase, SemanticKernelAgentBase
from common.contracts.common.answer import Answer
from common.contracts.configuration.orchestrator_config import (
    ResolvedOrchestratorConfig,
)
from common.contracts.orchestrator.request import Request
from common.contracts.orchestrator.response import Response
from common.sk_service.service_configurator import get_service
from common.telemetry.app_logger import AppLogger
from common.utilities.redis_message_handler import RedisMessageHandler

KERNEL_AZURE_CHAT_COMPLETION_SERVICE_ID = "kernel_completion_service"

# Initialize the update messages to be displayed to the user
update_messages = [
    "Aggregating relevant information for your request...",
    "Compiling data for your query...",
    "Generating plan to provide accurate results...",
]


@dataclass
class AgentRuntimeConfig:
    agent: Union[SemanticKernelAgentBase, AzureAIAgentBase]
    agent_thread: Union[ChatHistoryAgentThread, AzureAIAgentThread]


class AgentOrchestrator:
    def __init__(
        self,
        logger: AppLogger,
        message_handler: RedisMessageHandler,
        bing_resource_connection_id: str,
        configuration: ResolvedOrchestratorConfig = None,
    ) -> None:
        self.logger = logger
        self.message_handler = message_handler
        self.bing_resource_connection_id = bing_resource_connection_id

        # Semantic Kernel Settings
        self.kernel: Kernel = None
        self.project_client: AIProjectClient = None
        self.memory: SemanticTextMemory = None
        self.chat_history: ChatHistory = ChatHistory()

        # Create Agent threads
        self.search_query_generator_agent_thread: AzureAIAgentThread = None
        self.researcher_agent_thread: AzureAIAgentThread = None
        self.report_generator_agent_thread: AzureAIAgentThread = None
        self.report_comparator_agent_thread: AzureAIAgentThread = None

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
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()  # auto-invoke functions when available

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
        request_thread: AgentThread = await self.project_client.agents.threads.get(thread_id)
        self.logger.info(f"Thread {request_thread.id} retrieved successfully from Azure AI Foundry!")

        # Initialize agent threads
        self.search_query_generator_agent_thread = AzureAIAgentThread(
            client=self.project_client, thread_id=request_thread.id
        )
        self.researcher_agent_thread = AzureAIAgentThread(client=self.project_client, thread_id=request_thread.id)
        self.report_generator_agent_thread = AzureAIAgentThread(
            client=self.project_client, thread_id=request_thread.id
        )
        self.report_comparator_agent_thread = AzureAIAgentThread(
            client=self.project_client, thread_id=request_thread.id
        )

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
        if agent == Agent.SEARCH_QUERY_GENERATOR_AGENT:
            _agent = await self.agent_factory.create_search_query_generator_agent(
                kernel=self.kernel, configuration=agent_config
            )
        elif agent == Agent.RESEARCHER_AGENT:
            _agent = await self.agent_factory.create_researcher_agent(
                kernel=self.kernel,
                configuration=agent_config,
                bing_connection_id=self.bing_resource_connection_id,
            )
        elif agent == Agent.REPORT_GENERATOR_AGENT:
            _agent = await self.agent_factory.create_report_generator_agent(
                kernel=self.kernel,
                configuration=agent_config,
            )
        elif agent == Agent.REPORT_COMPARATOR_AGENT:
            _agent = await self.agent_factory.create_report_comparator_agent(
                kernel=self.kernel,
                configuration=agent_config,
                bing_connection_id=self.bing_resource_connection_id,
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

        # 1. SEARCH QUERY GENERATOR AGENT SETUP
        self.agent_runtime_config_map[Agent.SEARCH_QUERY_GENERATOR_AGENT] = await self.__create_agent(
            agent=Agent.SEARCH_QUERY_GENERATOR_AGENT,
            agent_thread=self.search_query_generator_agent_thread,
        )

        # 2. RESEARCHER AGENT SETUP
        self.agent_runtime_config_map[Agent.RESEARCHER_AGENT] = await self.__create_agent(
            agent=Agent.RESEARCHER_AGENT, agent_thread=self.researcher_agent_thread
        )

        # 3. REPORT GENERATOR AGENT SETUP
        self.agent_runtime_config_map[Agent.REPORT_GENERATOR_AGENT] = await self.__create_agent(
            agent=Agent.REPORT_GENERATOR_AGENT,
            agent_thread=self.report_generator_agent_thread,
        )

        # 4. REPORT COMPARATOR AGENT SETUP
        self.agent_runtime_config_map[Agent.REPORT_COMPARATOR_AGENT] = await self.__create_agent(
            agent=Agent.REPORT_COMPARATOR_AGENT,
            agent_thread=self.report_comparator_agent_thread,
        )

    async def start_agent_workflow(self, request: Request) -> Response:
        """
        Start the agent workflow by invoking agents.

        Args:
            request (Request): The request object containing user input and session information.

        Returns:
            Response: The response object containing the final answer.
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
                if (
                    not request.additional_metadata
                    or not request.additional_metadata.get("research_query")
                    or not request.additional_metadata.get("persona")
                ):
                    raise ValueError("Research query and persona is required.")

                # Check if the request is to compare reports
                if request.additional_metadata.get("action") == "compare":
                    return await self.handle_report_comparison_request(request)

                # Extract research query, persona, and report level from additional metadata
                research_query = request.additional_metadata.get("research_query")
                persona = request.additional_metadata.get("persona")
                report_level = request.additional_metadata.get(
                    "report_level", "1"
                )  # Default to level 1 if not provided

                await self.message_handler.send_update(
                    "Generating optimized queries for best results...",
                    request.dialog_id,
                )

                # Generate Search Queries
                search_query_generator_response = await self.__invoke_agent(
                    agent=Agent.SEARCH_QUERY_GENERATOR_AGENT,
                    messages=message,
                    kernel_arguments=KernelArguments(
                        research_query=research_query,
                        persona=persona,
                        report_level=report_level,
                        current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )

                # Format search queries for display
                search_queries = json.loads(search_query_generator_response.content.content)["search_queries"]
                search_queries_md = "\n".join([f"- {q}" for q in search_queries])
                self.logger.info(f"Generated search queries: {search_queries_md}")
                await self.message_handler.send_update(f"Searching Bing...\n\n{search_queries_md}", request.dialog_id)

                # Gather Research Data on the generated Search Queries
                researcher_response = await self.__invoke_agent(
                    agent=Agent.RESEARCHER_AGENT,
                    messages=message,
                    kernel_arguments=KernelArguments(
                        persona=persona,
                        report_level=report_level,
                        search_queries=search_queries,
                    ),
                )

                researcher_response_str = researcher_response.content.content
                self.logger.info(f"Report generated by Report Generator Agent: {researcher_response_str}")
                await self.message_handler.send_update(
                    "Search completed! Compiling Bing results and generating final report...",
                    request.dialog_id,
                )

                bing_grounding_metadata = await self._get_bing_grounding_metadata(
                    thread_id=self.researcher_agent_thread.id,
                    run_id=researcher_response.metadata.get("run_id", ""),
                )

                # Generate Final Report and return the response
                report = await self.__invoke_agent(
                    agent=Agent.REPORT_GENERATOR_AGENT,
                    messages=message,
                    kernel_arguments=KernelArguments(
                        research_data=researcher_response_str,
                        persona=request.additional_metadata.get("persona"),
                        report_level=request.additional_metadata.get(
                            "report_level", "1"
                        ),  # Default to level 1 if not provided
                    ),
                )

                self.logger.info(f"Final report generated: {report.content.content}")
                return Response(
                    session_id=request.session_id,
                    thread_id=request.thread_id,
                    dialog_id=request.dialog_id,
                    user_id=request.user_id,
                    answer=Answer(
                        answer_string=report.content.content,
                        is_final=True,
                        additional_metadata={
                            "research_query": research_query,
                            "persona": persona,
                            "report_level": report_level,
                            "bing_search_queries": bing_grounding_metadata,
                        },
                    ),
                    error=None,
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

    async def handle_report_comparison_request(self, request: Request) -> None:
        if not request.additional_metadata or not request.additional_metadata.get("report_content"):
            self.logger.error("Report comparison request is missing required metadata.")
            return Response(
                session_id=request.session_id,
                thread_id=request.thread_id,
                dialog_id=request.dialog_id,
                user_id=request.user_id,
                answer=Answer(
                    answer_string="Missing report content for comparison.",
                    is_final=True,
                ),
                error=None,
            )

        self.logger.info(f"Generating comparison report for the base report.")

        # Invoke the Report Comparator Agent to compare reports
        report_comparator_response = await self.__invoke_agent(
            agent=Agent.REPORT_COMPARATOR_AGENT,
            messages=ChatMessageContent(
                role=AuthorRole.USER,
                items=[TextContent(text="Generate a comparison report for the given base report.")],
            ),
            kernel_arguments=KernelArguments(
                base_report=request.additional_metadata.get("report_content"),
                created_at=request.additional_metadata.get("created_at"),
            ),
        )

        self.logger.info(f"Comparison report generated: {report_comparator_response.content.content}")

        bing_grounding_metadata = await self._get_bing_grounding_metadata(
            thread_id=self.report_comparator_agent_thread.id,
            run_id=report_comparator_response.metadata.get("run_id", ""),
        )

        return Response(
            session_id=request.session_id,
            thread_id=request.thread_id,
            dialog_id=request.dialog_id,
            user_id=request.user_id,
            answer=Answer(
                answer_string=report_comparator_response.content.content,
                is_final=True,
                additional_metadata={
                    "action": "compare",
                    "bing_search_queries": bing_grounding_metadata,
                },
            ),
            error=None,
        )

    async def _get_bing_grounding_metadata(self, thread_id: str, run_id: str) -> list:
        bing_search_queries = []

        try:
            # Fetch Agent Execution run steps to get Bing Grounding details
            run_steps = self.project_client.agents.run_steps.list(thread_id=thread_id, run_id=run_id)
            async for step in run_steps:
                step_details = step.get("step_details", {})
                tool_calls = step_details.get("tool_calls", [])

                if tool_calls:
                    for tool_call in tool_calls:
                        bing_grounding_details = tool_call.get("bing_grounding", {})
                        if bing_grounding_details:
                            # Extract the 'q' parameter from the Bing search URL
                            request_url = bing_grounding_details.get("requesturl", "")
                            parsed_url = urlparse(request_url)
                            query_params = parse_qs(parsed_url.query)
                            query = query_params.get("q", [""])[0]

                            bing_search_queries.append(
                                {
                                    "title": query,
                                    "url": f"https://www.bing.com/search?q={query}",
                                }
                            )
        except Exception as e:
            self.logger.exception(f"Error parsing Bing Grounding data: {e}. Skipping.")

        return bing_search_queries
