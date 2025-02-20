from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator

from common.contracts.common.overrides import Overrides
from common.contracts.common.user_profile import UserProfile
from common.contracts.common.user_prompt import UserPrompt


class ResponseMode(str, Enum):
    JSON = "json"
    AdaptiveCard = "adaptive_card"


class ChatRequest(BaseModel):
    conversation_id: str
    user_id: str = "anonymous"
    dialog_id: str
    message: UserPrompt
    user_profile: Optional[UserProfile] = None
    overrides: Overrides = Overrides()
    response_mode: Optional[ResponseMode] = ResponseMode.JSON

    @validator("user_id", pre=True, always=True)
    def set_default_user_id(cls, v):
        if not v or v.strip() == "":
            return "anonymous"
        return v
