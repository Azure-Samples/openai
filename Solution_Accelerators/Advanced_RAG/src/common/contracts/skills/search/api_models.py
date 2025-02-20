import json
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from typing import List, Optional, Union
from uuid import uuid4
from enum import Enum

from common.contracts.common.overrides import SearchOverrides


class FilterType(str, Enum):
    EQUALS = 'EQUALS'
    NOT_EQUALS = 'NOT_EQUALS'
    GREATER_OR_EQUALS = 'GREATER_OR_EQUALS'
    LESSER_OR_EQUALS = 'LESSER_OR_EQUALS'
    CONTAINS = "CONTAINS"

class LogicalOperator(str, Enum):
    AND = 'AND'
    OR = 'OR'

class SearchScenario(str, Enum):
    RAG = 'RAG'
    RETAIL = 'RETAIL'

class SearchFilter(BaseModel):
    field_name: str = Field(description="The name of the field from the search index to apply the requested filter.")
    field_value: str = Field(description="The value for the field_name to apply the requested filter.")
    filter_type: FilterType = Field(description="The type of filter to apply.")

    model_config = ConfigDict(use_enum_values=True)

class Filter(BaseModel):
    search_filters: List[SearchFilter] = Field(description="Search filter(s) to apply on the input search query.")
    logical_operator: Optional[LogicalOperator] = Field(description="The logical operator to apply in case of multiple filters.", default=None)

    model_config = ConfigDict(use_enum_values=True)

class SearchQuery(BaseModel):
    search_query: str = Field(description="Text search query to be used for searching closest matching products")
    filter: Optional[Filter] = Field(description="Categories of product to be used as filter to narrow down the search. Category must match exactly with existing product categories", default=None)
    min_results_count: int = Field(description="Minimum number of results to be returned by search query", default=1)
    max_results_count: int = Field(description="Maximum number of results to be returned by search query", default=3)
    search_id: str = Field(description="Id to be assign to the search query, resultId will be based on the search_id. If not provided an search_id is generated", default_factory=lambda: str(uuid4()))

class SearchRequest(BaseModel):
    search_queries: List[SearchQuery] = Field(
        description="Collection of search queries to be processed simultaneously",
        examples=[[
            {
                    "search_query": "baby outfit with light colors and with stripes",
                    "max_results_count": 2
            },
            {
                "search_query": "beach casual strapless dress",
                "max_results_count": 2,
                "category": ["Dress"],
                "search_id": "my-search-id-1"
            }
        ]]
    )
    search_overrides: Optional[SearchOverrides] = Field(
        description="Overrides for search queries",
        examples={
            "top": 5,
            "config_version": "1.0.1"
        }
    )

class SearchRagResult(BaseModel):
    id: str = Field(description="resultId from the result, extended from searchId")
    content: str = Field(description="Result text obtained from search query, mapped to search content field")
    section: Optional[str] = Field(description="Current section heading for this result text", default=None)
    headings: Optional[List[str]] = Field(description="List of headings for this result text", default=None)
    sourcePage: Optional[str] = Field(description="Source page for this result text", default=None)
    sourceFile: str = Field(description="Source file for this result text")
    category: str = Field(description="grouping for specific products")

    model_config = ConfigDict(extra='allow')

    def to_string(self) -> str:
        return f"{self.sourcePage}:{self.content}"

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "section": self.section,
            "headings": self.headings,
            "sourcePage": self.sourcePage,
            "sourceFile": self.sourceFile,
            "category": self.category
        }

class SearchRetailResult(BaseModel):
    id: str = Field(description="The unique identifier for the retail item")
    articleId: str = Field(description="The unique article id for the retail item")
    productName: str = Field(description="The name of the product")
    productType: str = Field(description="The product type for the retail item")
    indexGroupName: str = Field(description="The group name for the retail item")
    gender: str = Field(description="The gender associated with the retail item")
    detailDescription: str = Field(description="The detailed description for the retail item")
    summarizedDescription: str = Field(description="The summarized description for the retail item")
    imageUrl: str = Field(description="The resource locator for the image associated with the retail item")

    model_config = ConfigDict(extra='allow')

    def to_string(self) -> str:
        return f"{self.articleId}:{self.detailDescription}"

    def to_dict(self):
        return {
            "id": self.id,
            "articleId": self.articleId,
            "productName": self.productName,
            "productType": self.productType,
            "indexGroupName": self.indexGroupName,
            "gender": self.gender,
            "detailDescription": self.detailDescription,
            "summarizedDescription": self.summarizedDescription,
            "imageUrl": self.imageUrl
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
    
    def to_dict_for_prompt(self):
        return self.dict(include={
            "id", "articleId", "productName", "productType", "indexGroupName", "gender", "summarizedDescription"
        })

    def to_json_for_prompt(self) -> str:
        return json.dumps(self.to_dict_for_prompt())
    
class SearchResult(BaseModel):
    search_query: str = Field(description="Original text query used as search input")
    search_id: str = Field(description="SearchId of the search query")
    search_results: List[Union[SearchRagResult, SearchRetailResult]] = Field(description="Array of results obtained for the input search query")
    filter_succeeded: bool = Field(description="Flag to indicate if OpenAI filter was used or skipped", default=True)
    model_config = ConfigDict(extra='allow')
    search_score: Optional[float] = Field(description="Score of the search result", default=None)

    def to_string(self) -> List[str]:
        return [s.to_json() for s in self.search_results]

    def to_dict(self):
        return {
            "search_query": self.search_query,
            "search_id": self.search_id,
            "search_results": [search_result.to_dict() for search_result in self.search_results],
            "filter_succeeded": self.filter_succeeded,
            "search_score": self.search_score,
        }

class SearchResponse(BaseModel):
    results: List[SearchResult] = Field(description="Results of search queries")

    def to_dict(self):
        return {"results": [result.to_dict() for result in self.results]}