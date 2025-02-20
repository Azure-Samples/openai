from pydantic import BaseModel
from typing import List

class Analysis(BaseModel):
    image: str
    analysis: str

class AnalysisRequest(BaseModel):
    images: List[str]
    user_query: str

class AnalysisResponse(BaseModel):
    results: List[Analysis]