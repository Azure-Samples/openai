# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum


class StepNames(str, Enum):
    """Enum for available processing step names."""

    PROCESS_CONVERSATION = "PROCESS_CONVERSATION"
    SENTIMENT_ANALYSIS = "SENTIMENT_ANALYSIS"
    POST_CALL_ANALYSIS = "POST_CALL_ANALYSIS"
    CONSOLIDATE_INSIGHTS = "CONSOLIDATE_INSIGHTS"


class AgentNames(Enum):
    """Enum for agent names used in the process."""

    ASSIST_AGENT = "ASSIST_AGENT"
    SENTIMENT_ANALYSIS_AGENT = "SENTIMENT_ANALYSIS_AGENT"
    POST_CALL_ANALYSIS_AGENT = "POST_CALL_ANALYSIS_AGENT"


class FunctionNames(Enum):
    """Enum for function names used in the process."""

    PROCESS_CONVERSATION = "process_conversation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    POST_CALL_ANALYSIS = "post_call_analysis"
    CONSOLIDATE_INSIGHTS = "consolidate_insights"
