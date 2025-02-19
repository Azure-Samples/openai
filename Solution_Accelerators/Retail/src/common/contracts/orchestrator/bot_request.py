from typing import List, Optional

from pydantic import BaseModel

from common.contracts.common.overrides import Overrides
from common.contracts.common.user_profile import UserProfile


class BotRequest(BaseModel):
    connection_id: str
    user_id: str = "anonymous"
    conversation_id: str
    dialog_id: str
    messages: List[dict] = []
    locale: Optional[str] = None
    user_profile: Optional[UserProfile] = None
    overrides: Overrides = Overrides()
