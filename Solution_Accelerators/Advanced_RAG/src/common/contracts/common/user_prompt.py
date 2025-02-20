from enum import Enum
from typing import List, Optional

from pydantic import Base64Str, BaseModel


class PayloadType(str, Enum):
    IMAGE = "image"
    PRODUCT = "product"
    TEXT = "text"


class UserPromptPayload(BaseModel):
    type: PayloadType
    value: str  # either user utterance or base64 encoded image data
    locale: Optional[str] = None


"""User prompt contains text and image data in sequence they were added by the user"""


class UserPrompt(BaseModel):
    payload: List[UserPromptPayload] = []
