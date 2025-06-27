# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
"""
Azure DevOps MCP Server - Model Context Protocol server wrapper for Azure DevOps Tools.
This module provides an MCP server that exposes Azure DevOps functionality to GitHub Copilot.
"""

import asyncio
import json
import os
import sys
import logging
from typing import Any, Dict, List, Optional, Union, cast

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Add the parent directory to the Python path so we can import from tools
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from tools.azure_devops_tools import AzureDevOpsClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Azure DevOps client
azure_devops_client = AzureDevOpsClient()

# Initialize MCP
mcp_server = FastMCP(
    name="Azure DevOps Tools",
    instructions="Access Azure DevOps work items, features, commits, and other resources",
)


@mcp_server.tool(name="get_work_item", description="Get a work item by its ID.")
async def get_work_item(work_item_id: int, expand: str = "All") -> Dict[str, Any]:
    """
    Get a work item by its ID.

    Args:
        work_item_id: ID of the work item to retrieve
        expand: Level of detail to include ('None', 'Relations', 'Fields', 'All')

    Returns:
        Work item details
    """
    logger.info(f"Getting work item {work_item_id}")
    work_item = azure_devops_client.get_work_item(work_item_id, expand)

    # Convert to serializable format
    if hasattr(work_item, "as_dict"):
        return work_item.as_dict()
    return work_item


@mcp_server.tool(
    name="get_features_in_area_path", description="Get all feature work items within a specified area path."
)
async def get_features_in_area_path(area_path: str) -> List[Dict[str, Any]]:
    """
    Get all feature work items within a specified area path.

    Args:
        area_path: Area path to search within (e.g., 'MyProject\\Area\\SubArea')

    Returns:
        List of feature work items
    """
    logger.info(f"Getting features in area path {area_path}")
    work_items = azure_devops_client.get_features_in_area_path(area_path)

    # Convert to serializable format
    result = []
    for item in work_items:
        if hasattr(item, "as_dict"):
            result.append(item.as_dict())
        else:
            result.append(item)
    return result


@mcp_server.tool(
    name="search_work_items",
    description="Search for work items by text in title and description.",
)
async def search_work_items(
    search_text: str,
    work_item_types: Optional[List[str]] = None,
    states: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Search for work items by text.

    Args:
        search_text: Text to search for in work item title and description
        work_item_types: List of work item types to filter by (e.g., ['Feature', 'User Story'])
        states: List of states to filter by (e.g., ['Active', 'Resolved'])

    Returns:
        List of work items matching the search criteria
    """
    logger.info(f"Searching for work items with text '{search_text}'")
    work_items = azure_devops_client.search_work_items(search_text, work_item_types, states)

    # Convert to serializable format
    result = []
    for item in work_items:
        if hasattr(item, "as_dict"):
            result.append(item.as_dict())
        else:
            result.append(item)
    return result


@mcp_server.tool(name="get_related_commits", description="Get all commits related to a specific work item.")
async def get_related_commits(work_item_id: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all commits related to a specific work item.

    Args:
        work_item_id: ID of the work item

    Returns:
        Dictionary with pull requests and commits related to the work item
    """
    logger.info(f"Getting related commits for work item {work_item_id} in project")
    pull_requests, commits = azure_devops_client.get_related_commits(work_item_id)

    # Convert to serializable format
    pr_result = []
    for pr in pull_requests:
        if hasattr(pr, "as_dict"):
            pr_result.append(pr.as_dict())
        else:
            pr_result.append(pr)

    commit_result = []
    for commit in commits:
        if hasattr(commit, "as_dict"):
            commit_result.append(commit.as_dict())
        else:
            commit_result.append(commit)

    return {
        "pull_requests": pr_result,
        "commits": commit_result,
    }


@mcp_server.tool(name="get_work_items_by_tag", description="Get work items by a specific tag.")
async def get_work_items_by_tag(tag: str, work_item_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Get work items by a specific tag.

    Args:
        tag: Tag to search for
        work_item_types: List of work item types to filter by (e.g., ['Feature', 'User Story'])

    Returns:
        List of work items with the specified tag
    """
    logger.info(f"Getting work items with tag '{tag}'")
    work_items = azure_devops_client.get_work_items_by_tag(tag, work_item_types)

    # Convert to serializable format
    result = []
    for item in work_items:
        if hasattr(item, "as_dict"):
            result.append(item.as_dict())
        else:
            result.append(item)
    return result


@mcp_server.tool(name="get_linked_features", description="Get all features linked to a specific work item.")
async def get_linked_features(work_item_id: int) -> List[Dict[str, Any]]:
    """
    Get all features linked to a specific work item.

    Args:
        work_item_id: ID of the work item

    Returns:
        List of linked feature work items
    """
    logger.info(f"Getting linked features for work item {work_item_id} in project")
    linked_features = azure_devops_client.get_linked_features(work_item_id)

    # Convert to serializable format
    result = []
    for item in linked_features:
        if hasattr(item, "as_dict"):
            result.append(item.as_dict())
        else:
            result.append(item)
    return result


@mcp_server.tool(name="get_linked_documents", description="Get all documents linked to a specific work item.")
async def get_linked_documents(work_item_id: int) -> List[Dict[str, Any]]:
    """
    Get all documents linked to a specific work item.

    Args:
        work_item_id: ID of the work item

    Returns:
        List of linked document URLs and their titles
    """
    logger.info(f"Getting linked documents for work item {work_item_id} in project")
    documents = azure_devops_client.get_linked_documents(work_item_id)
    return documents


@mcp_server.tool(
    name="get_related_code_references",
    description="Get code references related to a work item, such as pull requests and branches.",
)
async def get_related_code_references(work_item_id: int) -> List[Dict[str, Any]]:
    """
    Get code references related to a work item, such as pull requests and branches.

    Args:
        work_item_id: ID of the work item

    Returns:
        List of related code references
    """
    logger.info(f"Getting related code references for work item {work_item_id}")
    references = azure_devops_client.get_related_code_references(work_item_id)
    return references


if __name__ == "__main__":
    mcp_server.run()
