from abc import ABC, abstractmethod
from typing import List
from common.contracts.data.prompt import Prompt
from pydantic import BaseModel

class Recommendations(ABC, BaseModel):
    @abstractmethod
    def get_recommendations(self) -> List[str]:
        pass

class RecommendationList(Recommendations):
    recommendations: List[str] = None

    def get_recommendations(self) -> List[str]: 
        return self.recommendations


SUPPORTED_STRUCTURED_OUTPUTS = {
    "RecommendationList": RecommendationList 
}
