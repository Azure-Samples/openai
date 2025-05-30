# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum


class Agent(Enum):
    """
    Enum for agent types used in the orchestrator.

    Attributes:
        JIRA_AGENT (str): Name of the JIRA agent.
        DEVOPS_AGENT (str): Name of the DevOps agent.
        VISUALIZATION_AGENT (str): Name of the Visualization agent.
        PLANNER_AGENT (str): Name of the Planner agent.
    """
    PLANNER_AGENT = "PLANNER_AGENT"
    JIRA_AGENT = "JIRA_AGENT"
    DEVOPS_AGENT = "DEVOPS_AGENT"
    VISUALIZATION_AGENT = "VISUALIZATION_AGENT"

    FALLBACK_AGENT = "FALLBACK_AGENT"