import time
from typing import List, Optional, Any
from pydantic import BaseModel

from common.contracts.data.prompt import LLMModelFamily

class LogProperties(BaseModel):
    application_name: Optional[str] = None
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    dialog_id: Optional[str] = None
    request: Optional[str] = None
    response: Optional[str] = None
    duration_ms: Optional[float] = -1.0
    start_time: Optional[float] = -1.0
    path: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.start_time = time.monotonic()
    
    def set_start_time(self):
        self.start_time = time.monotonic()

    def calculate_duration_ms(self):
        return (time.monotonic() - self.start_time) * 1000

    def model_dump(self):
        properties = {}
        if self.application_name:
            properties["ApplicationName"] = self.application_name
        if self.user_id:
            properties["user_id"] = self.user_id
        if self.conversation_id:
            properties["conversation_id"] = self.conversation_id
        if self.dialog_id:
            properties["dialog_id"] = self.dialog_id
        if self.request:
            properties["request"] = self.request
        if self.response:
            properties["response"] = self.response
        if self.path:
            properties["path"] = self.path
        properties["duration_ms"] = self.duration_ms
        return properties
    
    def record_duration_ms(self): 
        self.duration_ms = (time.monotonic() - self.start_time) * 1000

class HttpRequestLog(LogProperties):
    request_url: Optional[str] = 'Not set'
    method: Optional[str] = 'Not set'
    status_code: Optional[int] = -1

    def __init__(self, **data):
        super().__init__(**data)


    def model_dump(self):
        properties = super().model_dump()
        properties["request_url"] = self.request_url
        properties["method"] = self.method
        return properties


class AOAICallLog(BaseModel):
    log_message: str = 'AOAI Call'
    prompt_version: str = '1.0.0'
    prompt_nickname: str = 'Not Set in the config file'
    llm_model_family: Optional[LLMModelFamily] = None
    user_prompt: Optional[str] = 'User_Prompt not set'
    system_prompt: Optional[str] = 'System_Prompt not set'
    message_list: Optional[str] = ''
    llm_model_parameters: Optional[str] = ''
    finish_reason: Optional[str] = "Finish_Reason not set"
    llm_response: Optional[str] = "AOAI_Response not set"
    prompt_token_count: Optional[int] = -1
    completion_token_count: Optional[int] = -1
    total_token_count: Optional[int] = -1
    duration_ms: Optional[float] = -1.0

    def model_dump(self):
        return {
            "prompt_version": self.prompt_version,
            "prompt_nickname": self.prompt_nickname,
            "llm_model_family": self.llm_model_family.value if self.llm_model_family else None,
            "user_prompt": self.user_prompt,
            "system_prompt": self.system_prompt,
            "message_list": self.message_list,
            "llm_model_parameters": self.llm_model_parameters,
            "finish_reason": self.finish_reason,
            "llm_response": self.llm_response,
            "prompt_token_count": self.prompt_token_count,
            "completion_token_count": self.completion_token_count,
            "total_token_count": self.total_token_count,
            "duration_ms": self.duration_ms
        }
    
    
class OrchestratorRunLog(LogProperties):
    log_message: str = 'Finished orchestrator run'


class OrchestratorPlanLog(BaseModel):
    log_message: str = 'LinearOrchestrator run completed'
    plan_generation_duration_ms: Optional[float] = -1.0
    plan: Optional[List[str]] = []
    plan_execution_duration_ms: Optional[float] = -1.0
    final_answer_duration_ms: Optional[float] = -1.0

    def model_dump(self):
        return {
            "plan_generation_duration_ms": self.plan_generation_duration_ms,
            "plan": self.plan,
            "plan_execution_duration_ms": self.plan_execution_duration_ms,
            "final_answer_duration_ms": self.final_answer_duration_ms
        }

class PrunedSearchResultsLog(BaseModel):
    log_message: str = 'Pruned search results'
    original_search_results_count: Optional[int] = -1
    original_token_count: Optional[int] = -1
    history_token_count: Optional[int] = -1
    trimmed_search_results_count: Optional[int] = -1
    final_token_count: Optional[int] = -1

    def model_dump(self):
        return {
            "original_search_results_count": self.original_search_results_count,
            "original_token_count": self.original_token_count,
            "history_token_count": self.history_token_count,
            "trimmed_search_results_count": self.trimmed_search_results_count,
            "final_token_count": self.final_token_count
        }
    
class StaticOrchestratorLog(BaseModel):
    log_message: str = 'StaticOrchestrator run completed'
    
    search_request_generation_duration_ms: Optional[float] = -1.0
    search_requests: Optional[List[dict]] = ''

    search_duration_ms: Optional[float] = -1.0
    search_response: Optional[str] = ''
    search_response_code: Optional[int] = -1

    final_answer_duration_ms: Optional[float] = -1.0
    final_answer: Optional[str] = ''

    def model_dump(self):
        return {
            "search_duration_ms": self.search_duration_ms,
            "search_response": self.search_response,
            "search_response_code": self.search_response_code,
            "final_answer_duration_ms": self.final_answer_duration_ms,
            "final_answer": self.final_answer,
            "search_request_generation_duration_ms": self.search_request_generation_duration_ms,
            "search_requests": self.search_requests
        }

class MultimodalStaticOrchestratorLog(BaseModel):
    log_message: str = 'StaticOrchestrator run completed'

    classification_duration_ms: Optional[float] = -1.0
    classification_result: Optional[str] = ''

    describe_and_replace_images_duration_ms: Optional[float] = -1.0
    replaced_images_descriptions: Optional[List[str]] = ''

    recommender_duration_ms: Optional[float] = -1.0
    recommender_response: Optional[str] = ''
    recommender_response_code: Optional[int] = -1

    search_duration_ms: Optional[float] = -1.0
    search_response: Optional[str] = ''
    search_response_code: Optional[int] = -1

    final_answer: Optional[str] = ''
    final_answer_generation_duration_ms: Optional[float] = -1.0
    final_answer_generation_reasoning: Optional[str] = ''
    filtering_reasoning: Optional[str] = ''
    trimmed_search_results: Optional[str] = ''

    def model_dump(self):
        return {
            "classification_duration_ms": self.classification_duration_ms,
            "classification_result": self.classification_result,
            "describe_and_replace_images_duration_ms": self.describe_and_replace_images_duration_ms,
            "replaced_images_descriptions": self.replaced_images_descriptions,
            "recommender_duration_ms": self.recommender_duration_ms,
            "recommender_response": self.recommender_response,
            "recommender_response_code": self.recommender_response_code,
            "search_duration_ms": self.search_duration_ms,
            "search_response": self.search_response,
            "search_response_code": self.search_response_code,
            "final_answer": self.final_answer,
            "final_answer_generation_duration_ms": self.final_answer_generation_duration_ms,
            "final_answer_generation_reasoning": self.final_answer_generation_reasoning,
            "filtering_reasoning": self.filtering_reasoning,
            "trimmed_search_results": self.trimmed_search_results  
        }

class PlanStepLog(BaseModel):
    log_message: str = 'Step execution completed'
    step_name: Optional[str] = 'Step_Name not set'
    step_aoai_call_duration_ms: Optional[float] = -1.0
    step_request: Optional[str] = ''
    step_response: Optional[str] = ''
    step_execution_duration_ms: Optional[float] = -1.0

    def model_dump(self):
        return {
            "step_name": self.step_name,
            "step_aoai_call_duration_ms": self.step_aoai_call_duration_ms,
            "step_request": self.step_request,
            "step_response": self.step_response,
            "step_execution_duration_ms": self.step_execution_duration_ms
        }

class CreateConfigurationLog(LogProperties):
    log_message: str = 'Configuration created successfully'

