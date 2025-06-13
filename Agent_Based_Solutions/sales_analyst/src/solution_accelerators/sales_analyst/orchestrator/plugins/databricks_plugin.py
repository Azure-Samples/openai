# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from semantic_kernel.functions import kernel_function
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI
import json
from typing import Optional


class DatabricksPlugin:
    """
    Plugin for integrating with Databricks.
    Provides a kernel function to execute Databricks SQL queries.
    """

    def __init__(self, workspace_client: WorkspaceClient, space_id: str):
        """
        Initialize the DatabricksPlugin with a WorkspaceClient.

        Args:
            workspace_client (WorkspaceClient): The Databricks Workspace client.
        """
        self.workspace_client = workspace_client
        self.genie_api = GenieAPI(workspace_client.api_client)
        self.space_id = space_id

    @kernel_function(
        description="Genie is a virtual assistant that helps you interact with your data in Databricks. You can ask natural questions about your data, and Genie will provide answers based on the data available in your workspace. You can also pass in a conversation ID to continue an existing conversation.",
    )
    def ask_genie(self, question: str, conversation_id: Optional[str] = None) -> str:
        """
        Ask Genie a question and get a response.
        """
        try:
            if conversation_id is None:
                message = self.genie_api.start_conversation_and_wait(self.space_id, question)
                conversation_id = message.conversation_id
            else:
                message = self.genie_api.create_message_and_wait(self.space_id, conversation_id, question)

            query_result = None
            if message.query_result:
                query_result = self.genie_api.get_message_query_result(
                    self.space_id, message.conversation_id, message.id
                )

            message_content = self.genie_api.get_message(self.space_id, message.conversation_id, message.id)

            # Try to parse structured data if available
            if query_result and query_result.statement_response:
                statement_id = query_result.statement_response.statement_id
                results = self.workspace_client.statement_execution.get_statement(statement_id)
                columns = results.manifest.schema.columns
                data = results.result.data_array
                headers = [col.name for col in columns]
                rows = []
                for row in data:
                    formatted_row = []
                    for value, col in zip(row, columns):
                        if value is None:
                            formatted_value = "NULL"
                        elif col.type_name in ["DECIMAL", "DOUBLE", "FLOAT"]:
                            formatted_value = f"{float(value):,.2f}"
                        elif col.type_name in ["INT", "BIGINT", "LONG"]:
                            formatted_value = f"{int(value):,}"
                        else:
                            formatted_value = str(value)
                        formatted_row.append(formatted_value)
                    rows.append(formatted_row)
                return json.dumps({"conversation_id": conversation_id, "table": {"columns": headers, "rows": rows}})

            # Fallback to plain message text
            if message_content.attachments:
                for attachment in message_content.attachments:
                    if attachment.text and attachment.text.content:
                        return json.dumps({"conversation_id": conversation_id, "message": attachment.text.content})

            return json.dumps(
                {"conversation_id": conversation_id, "message": message_content.content or "No content returned."}
            )

        except Exception as e:
            return json.dumps({"error": "An error occurred while talking to Genie.", "details": str(e)})
