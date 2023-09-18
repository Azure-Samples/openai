from enum import Enum
from typing import List, Optional


class ApproachType(Enum):
    structured = "1"
    unstructured = "2"
    chit_chat = "3"
    continuation = "4"
    inappropriate = "5"


class Answer:
    def __init__(
        self,
        formatted_answer: str = "",
        query_generation_prompt: Optional[str] = None,
        query: Optional[str] = None,
        query_result: Optional[str] = None,
    ):
        self.formatted_answer = formatted_answer
        self.query_generation_prompt = query_generation_prompt
        self.query = query
        self.query_result = query_result

    def to_item(self):
        return {
            "formatted_answer": self.formatted_answer,
            "query_generation_prompt": self.query_generation_prompt,
            "query": self.query,
            "query_result": self.query_result,
        }


class ChatResponse:
    def __init__(
        self,
        answer: Answer,
        classification: Optional[ApproachType] = None,
        data_points: List[str] = [],
        error: Optional[str] = None,
        suggested_classification: Optional[ApproachType] = None,
        show_retry: bool = False,
    ):
        self.answer = answer
        self.classification = classification
        self.data_points = data_points
        self.error = error
        self.suggested_classification = suggested_classification
        self.show_retry = show_retry

    def to_item(self):
        return {
            "classification": self.classification.name
            if self.classification is not None
            else None,
            "answer": self.answer.to_item(),
            "data_points": [str(data_point) for data_point in self.data_points],
            "error": self.error,
            "suggested_classification": self.suggested_classification.value
            if self.suggested_classification is not None
            else None,
            "show_retry": self.show_retry,
        }
