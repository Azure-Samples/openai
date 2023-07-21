from typing import List

from backend.contracts.chat_response import ChatResponse


class Approach:
    def run(self, history: List[dict], overrides: dict) -> ChatResponse:
        raise NotImplementedError
