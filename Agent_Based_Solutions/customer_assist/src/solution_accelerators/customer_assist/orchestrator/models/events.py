# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum, auto


class ProcessInputEvent(Enum):
    """Events that can trigger the customer call assist process."""

    NEW_MESSAGE_RECEIVED = "NEW_MESSAGE_RECEIVED"
    CALL_ENDED = "CALL_ENDED"


class StepTriggerEvent(Enum):
    """Events that trigger specific steps in the process."""

    ANALYZE_SENTIMENT = "ANALYZE_SENTIMENT"
    PROCESS_CONVERSATION = "PROCESS_CONVERSATION"
    PERFORM_POST_CALL_ANALYSIS = "PERFORM_POST_CALL_ANALYSIS"
    CONSOLIDATE_INSIGHTS = "CONSOLIDATE_INSIGHTS"


class StepCompletionEvent(Enum):
    """Events emitted when steps complete their processing."""

    CONVERSATION_PROCESSED = "CONVERSATION_PROCESSED"
    SENTIMENT_ANALYZED = "ANALYZE_SENTIMENT_COMPLETED"
    POST_CALL_ANALYSIS_COMPLETED = "POST_CALL_ANALYSIS_COMPLETED"
    INSIGHTS_CONSOLIDATED = "INSIGHTS_CONSOLIDATED"


class ProcessCompletionEvent(Enum):
    """Events indicating overall process completion states."""

    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    ANALYSIS_FAILED = "ANALYSIS_FAILED"
