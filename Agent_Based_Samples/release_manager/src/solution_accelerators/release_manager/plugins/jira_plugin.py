# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from typing import Any, Optional

import requests
from jira import JIRA as JiraClient
from models.jira_settings import JiraSettings
from semantic_kernel.functions import kernel_function
from semantic_kernel.memory.semantic_text_memory import SemanticTextMemory

from common.telemetry.app_logger import AppLogger


class JiraPlugin:
    """
    A plugin for interacting with Jira using the JIRA Python library.
    """
    def __init__(
        self,
        logger: AppLogger,
        settings: JiraSettings,
        customfield_description_str: str,
        jql_instructions: str,
        memory: Optional[SemanticTextMemory] = None,
        memory_store_collection_name: Optional[str] = None,
    ):
        self.logger = logger

        self.settings = settings
        self.jira_client = JiraClient(
            server=settings.server_url,
            basic_auth=(settings.username, settings.password)
        )

        self.memory = memory
        self.memory_store_collection_name = memory_store_collection_name

        self.jql_instructions = jql_instructions
        self.custom_field_description_json = json.loads(customfield_description_str)
        self.jira_field_map = []

    def __fetch_jira_fields(self) -> str:
        self.logger.info(f"Fetching Jira fields from server {self.settings.server_url}")

        try:
            # Jira Client SDK does not support fetching fields directly.
            response = requests.get(f"{self.settings.server_url}/rest/api/2/field", auth=(self.settings.username, self.settings.password))
            response.raise_for_status()
            fields = response.json()

            # Only target fields that are in custom_field_description_json
            custom_field_names = {item.get("name") for item in self.custom_field_description_json}
            field_summary = ""
            for field in fields:
                name = field.get("name")
                if name not in custom_field_names:
                    continue

                id = field.get("id")
                type = field.get("schema", {}).get("type", "unknown")
                name = field.get("name")
                custom = field.get("custom", False)
                description = next((item.get("description", "") for item in self.custom_field_description_json if item.get("name") == name), "")

                summary = f"Field name: {name} - Id: {id} - Type: {type} - {'Custom' if custom else 'Standard'}"
                self.jira_field_map.append({
                    "id": id,
                    "name": name,
                    "type": type,
                    "custom": custom,
                    "description": description
                })

                if custom and description:
                    summary += f" - Description: {description}"

                field_summary += f"{summary}\n"

            return field_summary
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch Jira fields: {e}")
            return ""

    async def initialize(self):
        """
        Initialize the Jira plugin and hydrate memory with static information.
        """
        self.logger.info("Initializing Jira plugin..")

        if not self.memory or not self.memory_store_collection_name:
            self.logger.warning("Memory store/name is not provided. Skipping memory hydration.")
            return

        self.logger.info("Hydrating memory with Jira schema information.")

        # Fetch Jira fields and save to memory store
        field_summary = self.__fetch_jira_fields()
        if not field_summary:
            self.logger.warning("No Jira fields found. Skipping memory hydration for schema.")
        else:
            await self.memory.save_information(
                id="jira_fields_schema",
                collection=self.memory_store_collection_name,
                text=field_summary,
                description="Jira fields schema information containing field names, Ids, types, and descriptions.",
            )

        # Save JQL instructions to memory store
        if self.jql_instructions:
            await self.memory.save_information(
                id="jql_instructions",
                collection=self.memory_store_collection_name,
                text=self.jql_instructions,
                description="JQL instructions for querying Jira issues.",
            )

        self.logger.info("Jira plugin initialized successfully.")

    @kernel_function
    async def get_jira_field_info(self) -> str:
        """
        Get a summary of Jira fields including their names, IDs, types, and descriptions.

        Returns:
        str: A formatted string containing the field information.
        """
        if not self.memory:
            return self.custom_field_description_json

        result = await self.memory.search(
            collection=self.memory_store_collection_name,
            query="jira fields schema",
            limit=1
        )

        return result[0].text if result else "No Jira fields found."

    @kernel_function
    async def get_jira_jql_instructions(self) -> str:
        """
        Get JQL instructions for querying Jira issues.

        Returns:
        str: A formatted string containing the JQL instructions.
        """
        if not self.memory:
            return self.jql_instructions

        result = await self.memory.search(
            collection=self.memory_store_collection_name,
            query="jql instructions",
            limit=1
        )

        return result[0].text if result else "No Jira JQL instructions found."

    @kernel_function
    def create_issue(self, project_key: str, summary: str, description: str, issuetype: str) -> str:
        """
        Create a new issue in Jira.

        Args:
        project_key (str): The key of the project to create the issue in.
        summary (str): The summary of the issue.
        description (str): The description of the issue.
        issuetype (str): The type of the issue (e.g., 'Task', 'Bug', 'Story').

        Returns:
        str: The key of the newly created issue.
        """
        issue_dict = {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": issuetype},
        }
        new_issue = self.jira_client.create_issue(fields=issue_dict)

        self.logger.info(f"Issue created: {new_issue.key}")
        return new_issue.key

    @kernel_function
    def search_issues(self, jql_query: str) -> Any:
        """
        Search for issues in Jira using a JQL query.

        Args:
        jql_query (str): The JQL query to search for issues.

        Returns:
        list: A list of issue keys that match the JQL query.
        """
        self.logger.info(f"Searching for issues with JQL: {jql_query}")
        issues = self.jira_client.search_issues(jql_query)

        formatted_issues = []
        for issue in issues:
            issue_data = {
                "key": issue.key,
                "fields": {
                    field["name"]: issue.raw["fields"].get(field["id"])
                    for field in self.jira_field_map
                    if issue.raw["fields"].get(field["id"]) is not None
                },
            }
            formatted_issues.append(issue_data)

        self.logger.info(f"Found {len(formatted_issues)} issues")
        return formatted_issues

    @kernel_function
    def update_issue(self, issue_key: str, field: str, value):
        """
        Update an existing issue in Jira.

        Args:
        issue_key (str): The key of the issue to update.
        field (str): The field to update.
        value: The new value for the field.

        Returns:
        str: The key of the updated issue.
        """
        issue = self.jira_client.issue(issue_key)
        issue.update(fields={field: value})

        self.logger.info(f"Issue updated: {issue.key} - {field}: {value}")
        return issue.key
