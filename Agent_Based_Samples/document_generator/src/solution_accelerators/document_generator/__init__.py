# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
"""
Model Context Protocol (MCP) server for Azure DevOps (and future support for Sharepoint).
"""

from .tools.azure_devops_tools import AzureDevOpsClient

__all__ = [
    "AzureDevOpsClient",
]
