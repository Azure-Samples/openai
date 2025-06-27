#  Copyright (c) Microsoft Corporation.
#  Licensed under the MIT license.

import os
import json
from azure.identity.aio import DefaultAzureCredential

from opentelemetry.trace import Tracer

from azure.ai.projects.aio import AIProjectClient
from azure.ai.agents.models import ToolSet, SharepointTool
from azure.ai.agents.telemetry import AIAgentsInstrumentor
from common.telemetry.app_logger import AppLogger

class SharePointAgent:

    def __init__(self):
        """
        Initialize the SharePointAgent class.
        Note: This doesn't actually set up the agent - use the create() class method instead.
        """
        self.logger = None
        self.tracer = None
        self.project_client = None
        self.agent = None
        self.thread = None

        AIAgentsInstrumentor().instrument()
        
    @classmethod
    async def initialize(cls, logger: AppLogger, tracer: Tracer, sharepoint_connection_name: str = None):
        """
        Factory method to create and initialize a SharePoint agent with the specified SharePoint connection name.
        
        Args:
            sharepoint_connection_name (str): The name of the SharePoint connection to use.
            
        Returns:
            SharePointAgent: An initialized SharePointAgent instance
        """
        instance = cls()
        instance.logger = logger
        instance.tracer = tracer
        async with DefaultAzureCredential() as credential:
            instance.project_client = AIProjectClient(endpoint=os.getenv("AZURE_AI_PROJECT_ENDPOINT"), credential=credential)
            instance.agent = await instance._create_sharepoint_agent(sharepoint_connection_name=sharepoint_connection_name or os.getenv("SHAREPOINT_CONNECTION_NAME"))
            instance.thread = await instance.project_client.agents.threads.create()
        return instance

    async def _create_sharepoint_agent(self, sharepoint_connection_name: str):
        """
        Creates a SharePoint agent with the specified connection name.

        Args:
            sharepoint_connection_name (str): The name of the SharePoint connection to use. 
        """
        with self.tracer.start_as_current_span("create_sharepoint_agent"):
            if not sharepoint_connection_name:
                raise ValueError(
                    "SharePoint connection name must be provided."
                    "Either provide them explicitly or set the environment variable SHAREPOINT_CONNECTION_NAME."
                )
            
            sharepoint_connection_id = None
            async for conn in self.project_client.connections.list():
                if conn.name == sharepoint_connection_name:
                    sharepoint_connection_id = conn.id
                    break

            if not sharepoint_connection_id:
                raise ValueError(
                    "Please provide a valid SharePoint connection name. " 
                    f"No connection found with name: {sharepoint_connection_name}"
                )

            toolset = ToolSet()
            toolset.add(SharepointTool(connection_id=sharepoint_connection_id))

            sharepoint_agent = await self.project_client.agents.create_agent(
                model=os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"),
                name="sharepoint_agent",
                instructions="""
                You are a specialized assistant that retrieves and processes documents from SharePoint based on user queries.
                
                ## Your Capabilities
                - Search for documents in SharePoint based on relevant keywords
                - Retrieve document content from SharePoint sites
                - Extract key information from documents
                - Provide accurate summaries focused on the user's query
                
                ## How to Process Queries
                1. Analyze the query to identify key search terms
                2. Use the SharePoint tool to search for relevant documents
                3. Retrieve the most relevant documents using the tool
                4. Read and understand the document content
                5. Extract the information directly relevant to the user's query
                6. Synthesize a clear, concise response that directly addresses the query

                ## Response Format
                - Start with a direct answer to the query
                - Provide supporting details from the documents
                - When appropriate, structure information with bullets or numbered lists
                - For complex information, use sections with headings
                
                ## Important Guidelines
                - Be accurate and factual - only report information found in the documents
                - Never fabricate information
                - Focus on relevance - tailor your response directly to the query

                ## Note
                - Your responses should be based solely on the documents retrieved from SharePoint
                - Your response should be plain text
                - Do not use any Unicode characters that can not be rendered in plain text. such as emojis or special characters like '【' or '】'
                """,
                toolset=toolset
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
            if annotation.type == 'url_citation':
                sharepoint_annotations.append({
                    "url_citation": annotation.url_citation.url,
                })
        return sharepoint_annotations

    async def invoke_sharepoint_agent(self, agent_id: str, thread_id: str, query: str):
        """
        Invoke the SharePoint agent with a user query.

        Args:
            agent_id (str): The ID of the SharePoint agent to invoke.
            thread_id (str): The ID of the thread to use for the invocation.
            query (str): User query to process
        """
        with self.tracer.start_as_current_span(f"Invoking_sharepoint_agent_with_query_eq_{query}"):
            try:
                self.logger.info(f"Invoking SharePoint Agent with query: {query}")
                message = await self.project_client.agents.messages.create(
                    thread_id=thread_id,
                    content=query,
                    role="user"
                )

                run = await self.project_client.agents.runs.create_and_process(
                    thread_id=thread_id,
                    agent_id=agent_id,
                )

                if run.status == "failed":
                    self.logger.error(f"SharePoint agent run failed: {run.last_error}")
                    # If the run failed, return an empty string to not disrupt the flow for copilot
                    return ""

                async for message in self.project_client.agents.messages.list(thread_id=thread_id):
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
                self.logger.error(f"Error invoking SharePoint agent: {str(e)}")
                raise e