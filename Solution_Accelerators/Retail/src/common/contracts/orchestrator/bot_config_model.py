from pydantic import BaseModel
from common.contracts.data.prompt import Prompt

class RAGOrchestratorBotConfig(BaseModel):
    final_answer_generation_prompt: Prompt
    static_user_query_rephraser_prompt: Prompt


class RetailOrchestratorBotConfig(BaseModel):
    static_retail_classifier: Prompt
    static_retail_final_answer_generation: Prompt
