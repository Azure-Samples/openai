from backend.cognition.openai_client import OpenAIClient
from backend.contracts.chat_response import ChatResponse
from typing import Dict, List, Optional

class Approach:
    def run(self, history: List[Dict[str, str]], bot_config: dict, openai_client: OpenAIClient, overrides: Optional[dict] = None) -> ChatResponse:
        raise NotImplementedError
