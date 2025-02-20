from pydantic import BaseModel
from typing import List, Optional


class RecommenderResult(BaseModel):
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    dialog_id: Optional[str] = None
    recommendations: List[str]


class RecommenderRequest(BaseModel):
    descriptions: Optional[List[str]] = None
    recommendation_query: str

class RecommenderResponse(BaseModel):
    result: RecommenderResult

class CategoriesResponse(BaseModel):
    results: List[str]

class CategorySummary(BaseModel):
    category: str
    summary: str

class CategoriesWithSummaryResponse(BaseModel):
    results: List[CategorySummary]