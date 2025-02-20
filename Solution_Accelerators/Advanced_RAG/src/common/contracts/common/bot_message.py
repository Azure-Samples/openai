import json
from typing import Any

from pydantic import BaseModel

"""This class represents the final response from the bot to the user"""


class BotMessage(BaseModel, extra="allow"):
    payload: Any
    role: str = "assistant"
    # timestamp: AwareDatetime = dt.now(timezone.utc) # TODO: has issues with serialization throws error when sending via http post. commented out for now

    """Helper method to convert bot response to string for passing as history to text based GPT models"""

    # TODO: should this go to extension class where this is implemented as an extension method?
    def get_bot_response_str(self) -> str:
        return json.dumps(self.payload)
