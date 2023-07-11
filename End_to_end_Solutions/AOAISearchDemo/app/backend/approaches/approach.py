from backend.contracts.chat_response import ChatResponse
from typing import List

class Approach:
    def run(self, history: List[dict], overrides: dict) -> ChatResponse:
        raise NotImplementedError
