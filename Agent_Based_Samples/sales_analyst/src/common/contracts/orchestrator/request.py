# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pydantic import BaseModel, field_validator, validator
from typing import Any, Dict, List, Optional

from common.contracts.common.user_profile import UserProfile
from common.contracts.common.overrides import Overrides


class Request(BaseModel):
    """
    Represents a request to the orchestrator, containing user input and context information.

    Attributes:
        trace_id (Optional[dict[str, str]]): Optional trace ID for tracking the request.
        session_id (str): Unique identifier for the session.
        dialog_id (str): Unique identifier for the dialog.
        user_id (str): Identifier for the user, defaults to "anonymous".
        thread_id (str): Identifier for the thread of conversation.
        message (str): The user message.
        authorization (Optional[str]): Optional authorization token for the request.
        locale (Optional[str]): Locale of the user query, if specified.
        user_profile (Optional[UserProfile]): Optional user profile information.
        additional_metadata (Dict[str, Any]): Additional metadata for the request.
    """

    trace_id: Optional[dict[str, str]] = None
    session_id: str
    dialog_id: str
    user_id: str = "anonymous"
    thread_id: str
    message: str
    authorization: Optional[str] = None
    locale: Optional[str] = None
    user_profile: Optional[UserProfile] = None
    overrides: Overrides | None = None
    # The following fields are optional and can be used for additional metadata specific to the use-case.
    # They can be set to None if not needed.
    additional_metadata: Dict[str, Any] | None = None
