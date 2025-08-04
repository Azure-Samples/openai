# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
"""
Azure DevOps Tools - Utility functions for interacting with Azure DevOps APIs.
This module provides functions to retrieve work items, features, and related information
from Azure DevOps repositories.
"""

import os
import re
from typing import Dict, List, Optional, Set, Any, Union
from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking import WorkItemTrackingClient
from azure.devops.v7_1.git import GitClient
from azure.devops.v7_1.git.models import GitQueryCommitsCriteria, GitCommit, GitPullRequest
from azure.devops.v7_1.work_item_tracking.models import TeamContext, WorkItemQueryResult
from msrest.authentication import BasicAuthentication
import logging
from urllib.parse import unquote
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)


class AzureDevOpsClient:
    """
    Client to interact with Azure DevOps API to retrieve work items and related information.
    """

    def __init__(self, org_url: str = None, personal_access_token: str = None):
        """
        Initialize the Azure DevOps client.

        Args:
            org_url: Azure DevOps organization URL (e.g., 'https://dev.azure.com/myorg')
            personal_access_token: PAT for authentication
        """
        # Load environment variables if no explicit credentials are provided
        load_dotenv()

        self.org_url = org_url or os.getenv("AZURE_DEVOPS_ORG_URL")
        self.pat = personal_access_token or os.getenv("AZURE_DEVOPS_PAT")
        self.project = os.getenv("AZURE_DEVOPS_PROJECT")

        if not self.org_url or not self.pat:
            raise ValueError(
                "Azure DevOps organization URL and personal access token are required. "
                "Either provide them explicitly or set AZURE_DEVOPS_ORG_URL and "
                "AZURE_DEVOPS_PAT environment variables."
            )

        # Create a connection to Azure DevOps
        credentials = BasicAuthentication("", self.pat)
        self.connection = Connection(base_url=self.org_url, creds=credentials)

        # Get clients
        self.wit_client: WorkItemTrackingClient = self.connection.clients.get_work_item_tracking_client()
        self.git_client: GitClient = self.connection.clients.get_git_client()

    def get_work_item(self, work_item_id: int, expand: str = "All") -> Dict:
        """
        Get a work item by its ID.

        Args:
            work_item_id: ID of the work item to retrieve
            expand: Level of detail to include ('None', 'Relations', 'Fields', 'All')

        Returns:
            Work item details
        """
        try:
            work_item = self.wit_client.get_work_item(work_item_id, project=self.project, expand=expand)
            return work_item
        except Exception as e:
            logger.error(f"Error getting work item {work_item_id}: {str(e)}")
            return {}

    def get_features_in_area_path(self, area_path: str) -> List[Dict]:
        """
        Get all feature work items within a specified area path.

        Args:
            area_path: Area path to search within (e.g., 'MyProject\\Area\\SubArea')

        Returns:
            List of feature work items
        """
        # WIQL query to get features in the specified area path
        wiql = f"""
        SELECT [System.Id], [System.Title], [System.State], [System.Tags]
        FROM WorkItems
        WHERE [System.WorkItemType] = 'Feature' 
        AND [System.AreaPath] UNDER '{area_path}'
        ORDER BY [System.Id]
        """

        try:
            # Execute the query
            query_result: WorkItemQueryResult = self.wit_client.query_by_wiql(
                {"query": wiql}, team_context=TeamContext(project=self.project)
            )

            if not query_result.work_items:
                logger.info(f"No features found in area path {area_path}")
                return []

            # Get the work items
            work_item_ids = [work_item.id for work_item in query_result.work_items]
            work_items = self.wit_client.get_work_items(work_item_ids, project=self.project, expand="All")

            return work_items
        except Exception as e:
            logger.error(f"Error getting features in area path {area_path}: {str(e)}")
            return []

    def get_linked_features(self, work_item_id: int) -> List[Dict]:
        """
        Get all features linked to a specific work item.

        Args:
            work_item_id: ID of the work item

        Returns:
            List of linked feature work items
        """
        try:
            # Get the work item with its relations
            work_item = self.wit_client.get_work_item(work_item_id, project=self.project, expand="All")

            if not work_item or not hasattr(work_item, "relations"):
                return []

            linked_work_item_ids = set()

            # Extract linked work item IDs
            for relation in work_item.relations:
                # Check if the relation is to another work item
                if "workItems" in relation.url:
                    # Extract the ID from the URL
                    linked_id = int(relation.url.split("/")[-1])
                    linked_work_item_ids.add(linked_id)

            # Fetch all linked items
            linked_items = []
            if linked_work_item_ids:
                all_linked_items = self.wit_client.get_work_items(list(linked_work_item_ids), project=self.project)

                # Filter to keep only features
                linked_items = [
                    item for item in all_linked_items if item.fields.get("System.WorkItemType") == "Feature"
                ]

            return linked_items
        except Exception as e:
            logger.error(f"Error getting linked features for work item {work_item_id}: {str(e)}")
            return []

    def get_linked_documents(self, work_item_id: int) -> List[Dict]:
        """
        Get all documents linked to a specific work item.

        Args:
            work_item_id: ID of the work item

        Returns:
            List of linked document URLs and their titles
        """
        try:
            # Get the work item with its relations
            work_item = self.wit_client.get_work_item(work_item_id, project=self.project, expand="All")

            if not work_item or not hasattr(work_item, "relations"):
                return []

            linked_documents = []

            # Extract linked document information
            for relation in work_item.relations:
                # Check for hyperlinks or attachments
                if relation.rel in ["Hyperlink", "AttachedFile"]:
                    document_info = {
                        "url": relation.url,
                        "title": relation.attributes.get("name", "Untitled Document"),
                        "comment": relation.attributes.get("comment", ""),
                        "type": relation.rel,
                    }
                    linked_documents.append(document_info)

            return linked_documents
        except Exception as e:
            logger.error(f"Error getting linked documents for work item {work_item_id}: {str(e)}")
            return []

    def get_work_items_by_tag(self, tag: str, work_item_types: List[str] = None) -> List[Dict]:
        """
        Get work items by a specific tag.

        Args:
            tag: Tag to search for
            work_item_types: List of work item types to filter by (e.g., ['Feature', 'User Story'])

        Returns:
            List of work items with the specified tag
        """
        try:
            # Default to all main work item types if none provided
            if not work_item_types:
                work_item_types = ["Epic", "Feature", "User Story", "Bug", "Task"]

            # Create the work item type filter
            work_item_type_filter = " OR ".join([f"[System.WorkItemType] = '{wit}'" for wit in work_item_types])

            # WIQL query to get work items with the specified tag
            wiql = f"""
            SELECT [System.Id], [System.Title], [System.State], [System.Tags]
            FROM WorkItems
            WHERE ({work_item_type_filter})
            AND [System.Tags] CONTAINS '{tag}'
            ORDER BY [System.Id]
            """

            # Execute the query
            query_result = self.wit_client.query_by_wiql(
                {"query": wiql}, team_context=TeamContext(project=self.project)
            )

            if not query_result.work_items:
                logger.info(f"No work items found with tag '{tag}'")
                return []

            # Get the work items
            work_item_ids = [work_item.id for work_item in query_result.work_items]
            work_items = self.wit_client.get_work_items(work_item_ids, project=self.project)

            return work_items
        except Exception as e:
            logger.error(f"Error getting work items with tag '{tag}': {str(e)}")
            return []

    def search_work_items(
        self,
        search_text: str,
        work_item_types: Optional[List[str]] = None,
        states: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Search for work items by text.

        Args:
            search_text: Text to search for in work item title and description
            work_item_types: List of work item types to filter by (e.g., ['Feature', 'User Story'])
            states: List of states to filter by (e.g., ['Active', 'Resolved'])

        Returns:
            List of work items matching the search criteria
        """
        try:
            filters = []

            # Add work item type filter if provided
            if work_item_types:
                work_item_type_filter = " OR ".join([f"[System.WorkItemType] = '{wit}'" for wit in work_item_types])
                filters.append(f"({work_item_type_filter})")

            # Add state filter if provided
            if states:
                state_filter = " OR ".join([f"[System.State] = '{state}'" for state in states])
                filters.append(f"({state_filter})")

            # Combine filters with AND
            filter_clause = " AND ".join(filters)

            # Add the filter clause to the query if filters exist
            filter_string = f"AND {filter_clause} " if filter_clause else ""

            # WIQL query to search for work items
            wiql = f"""
            SELECT [System.Id], [System.Title], [System.State]
            FROM WorkItems
            WHERE (
                [System.Title] CONTAINS '{search_text}'
                OR [System.Description] CONTAINS '{search_text}'
            )
            {filter_string}
            ORDER BY [System.Id]
            """

            # Execute the query
            query_result = self.wit_client.query_by_wiql(
                {"query": wiql}, team_context=TeamContext(project=self.project)
            )

            if not query_result.work_items:
                logger.info(f"No work items found matching search text '{search_text}'")
                return []

            # Get the work items
            work_item_ids = [work_item.id for work_item in query_result.work_items]
            work_items = self.wit_client.get_work_items(work_item_ids, project=self.project, expand="All")

            return work_items
        except Exception as e:
            logger.error(f"Error searching for work items with text '{search_text}': {str(e)}")
            return []

    def get_related_commits(self, work_item_id: int) -> List[Dict]:
        """
        Get all commits related to a specific work item.

        Args:
            work_item_id: ID of the work item

        Returns:
            List of related commits
        """
        try:
            work_item = self.wit_client.get_work_item(id=work_item_id, expand="relations")

            pull_requests: List[GitPullRequest] = []
            commits: List[GitCommit] = []

            # Look through relations for PR links
            if work_item.relations:
                for relation in work_item.relations:
                    if relation.rel == "ArtifactLink":
                        artifact_url = relation.url
                        if "pullrequestid" in artifact_url.lower():
                            parts = unquote(artifact_url).split("/")
                            pr_id = parts[-1]
                            repo_id = parts[-2]
                            pull_requests.append(
                                self.git_client.get_pull_request(
                                    repository_id=repo_id, pull_request_id=pr_id, project=self.project
                                )
                            )

                        elif "commit" in artifact_url.lower():
                            parts = unquote(artifact_url).split("/")
                            commit_id = parts[-1]
                            repo_id = parts[-2]
                            commits.append(
                                self.git_client.get_commit(
                                    repository_id=repo_id, commit_id=commit_id, project=self.project
                                )
                            )
            return pull_requests, commits
        except Exception as e:
            logger.error(f"Error getting related commits for work item {work_item_id}: {str(e)}")
            return [], []

    def get_feature_dependencies(self, feature_id: int) -> List[Dict]:
        """
        Get features that are dependencies of the specified feature.

        Args:
            feature_id: ID of the feature work item

        Returns:
            List of dependent feature work items
        """
        try:
            # WIQL query to get dependencies of the feature
            wiql = f"""
            SELECT 
                [System.Id], 
                [System.Title], 
                [System.WorkItemType], 
                [System.State]
                FROM workitemLinks
                WHERE 
                    [Target].[System.Id] = {feature_id}
                    AND [System.Links.LinkType] = 'System.LinkTypes.Dependency-Forward'
            """

            # Execute the query
            query_result = self.wit_client.query_by_wiql(
                {"query": wiql}, team_context=TeamContext(project=self.project)
            )

            if not query_result.work_item_relations:
                logger.info(f"No dependencies found for feature {feature_id}")
                return []

            # Extract work item IDs from the relationships
            work_item_ids = []
            for relation in query_result.work_item_relations:
                if relation.target and relation.target.id:
                    work_item_ids.append(relation.target.id)

            # Get the work items
            if work_item_ids:
                work_items = self.wit_client.get_work_items(work_item_ids, project=self.project)
                return work_items

            return []
        except Exception as e:
            logger.error(f"Error getting dependencies for feature {feature_id}: {str(e)}")
            return []

    def get_related_code_references(self, work_item_id: int) -> List[Dict]:
        """
        Get code references related to a work item, such as pull requests and branches.

        Args:
            work_item_id: ID of the work item

        Returns:
            List of related code references
        """
        try:
            # Get the work item with its relations
            work_item = self.wit_client.get_work_item(work_item_id, project=self.project, expand="All")

            if not work_item or not hasattr(work_item, "relations"):
                return []

            code_references = []

            # Extract relevant code reference information
            for relation in work_item.relations:
                reference_type = None

                # Check for pull request
                if "pullRequests" in relation.url:
                    reference_type = "PullRequest"
                    pr_id = relation.url.split("/")[-1]
                    code_references.append(
                        {
                            "type": reference_type,
                            "id": pr_id,
                            "title": relation.attributes.get("name", f"Pull Request {pr_id}"),
                            "url": relation.url,
                        }
                    )
                # Check for branch
                elif "refs" in relation.url and "heads" in relation.url:
                    reference_type = "Branch"
                    branch_name = relation.url.split("/")[-1]
                    code_references.append(
                        {
                            "type": reference_type,
                            "name": branch_name,
                            "title": relation.attributes.get("name", branch_name),
                            "url": relation.url,
                        }
                    )
                # Check for build
                elif "build" in relation.url:
                    reference_type = "Build"
                    build_id = relation.url.split("/")[-1]
                    code_references.append(
                        {
                            "type": reference_type,
                            "id": build_id,
                            "title": relation.attributes.get("name", f"Build {build_id}"),
                            "url": relation.url,
                        }
                    )

            return code_references
        except Exception as e:
            logger.error(f"Error getting related code references for work item {work_item_id}: {str(e)}")
            return []
