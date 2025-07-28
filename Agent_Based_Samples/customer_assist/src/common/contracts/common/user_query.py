# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class PayloadType(str, Enum):
    """
    Enum representing the type of payload in a user query.
    It can be either 'image' for image data or 'text' for text data.
    """

    IMAGE = "image"
    TEXT = "text"


class UserQueryPayload(BaseModel):
    """
    Represents a single payload in a user query, which can be either text or image data.
    """

    type: PayloadType
    value: str  # either user text query or base64 encoded image data
    locale: Optional[str] = None


class UserQuery(BaseModel):
    """
    Represents a user query containing text or image data."
    """

    payload: List[UserQueryPayload] = []
