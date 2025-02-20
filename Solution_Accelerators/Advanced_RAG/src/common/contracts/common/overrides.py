from pydantic import BaseModel
from typing import Optional

class SearchOverrides(BaseModel):
    semantic_ranker: Optional[bool] = True
    vector_search: Optional[bool] = True
    top: Optional[int]  = None
    config_version: Optional[str] = None

class OrchestratorServiceOverrides(BaseModel):
    search_results_merge_strategy: str = "basic"
    config_version: Optional[str] = None

class SessionManagerServiceOverrides(BaseModel):
    check_safe_image_content: Optional[bool] = True
    config_version: Optional[str] = None

class Overrides(BaseModel):
    search_overrides: Optional[SearchOverrides] = SearchOverrides()
    orchestrator_runtime: Optional[OrchestratorServiceOverrides] = None
    session_manager_runtime: Optional[SessionManagerServiceOverrides] = None