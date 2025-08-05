# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum


class Agent(Enum):
    """
    Enum for agent types used in the orchestrator.
    """
    SEARCH_QUERY_GENERATOR_AGENT = "SEARCH_QUERY_GENERATOR_AGENT"
    RESEARCHER_AGENT = "RESEARCHER_AGENT"
    REPORT_GENERATOR_AGENT = "REPORT_GENERATOR_AGENT"
    REPORT_COMPARATOR_AGENT = "REPORT_COMPARATOR_AGENT"