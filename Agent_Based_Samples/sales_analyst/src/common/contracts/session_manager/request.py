# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from common.contracts.common.user_profile import UserProfile
from common.contracts.common.user_query import UserQuery


class ResponseMode(str, Enum):
    """
    Enum for response modes supported by the session manager.
    """

    JSON = "json"


class Request(BaseModel):
    """
    Request model for the session manager to handle user queries.

    Attributes:
        dialog_id (str): Unique identifier for the dialog.
        user_id (Optional[str]): Identifier for the user, defaults to "anonymous".
        message (UserQuery): The user query message.
        user_profile (Optional[UserProfile]): Optional user profile information.
        response_mode (Optional[ResponseMode]): Mode of response, defaults to JSON.
        additional_metadata (Optional[dict]): Additional metadata for the request.
        authorization (Optional[str]): Optional authorization token for the request.
    """

    dialog_id: str
    user_id: Optional[str] = "anonymous"
    message: UserQuery
    user_profile: Optional[UserProfile] = None
    response_mode: Optional[ResponseMode] = ResponseMode.JSON
    additional_metadata: Optional[dict] = None
    authorization: Optional[str] = None
