from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict  # Import the Dict type

class LLMModelFamily(str, Enum):
    AzureOpenAI = "AzureOpenAI"
    Phi3 = "Phi3"

class History(BaseModel):
    include: bool=False
    length: int=0
    filter: Optional[str] = None

class PromptConfig(BaseModel):
    template: str
    arguments: List[str] = []
    history: History = History()

    # update the template with the arguments passed as a dictionary
    def update_template_with_args(self, argument_dict: Dict) -> str:
        template = self.template
        for key in self.arguments:
            template = template.replace("{" + key + "}", argument_dict[key])
        
        return template

class ModelParameter(BaseModel):
    model_config = ConfigDict(extra='allow')  # Set to 'allow' to allow extra fields
    
    deployment_name: str|None = None
    temperature: float = 0.9
    max_tokens: int = 500

class ModelResponseFormat(BaseModel):
    format: Optional[dict[str,str]] = None
    response_schema: Optional[str] = None
    
    def get_response_format(self, supported_schemas: dict[str, BaseModel] = None):
        """
        Determines the response format based on the provided format, schema and supported schemas.
        Args:
            supported_schemas (dict[str, BaseModel], optional): A dictionary of supported schemas where the key is the schema name and the value is the corresponding BaseModel. Defaults to None.
        Returns:
            tuple: A tuple containing the format (or schema) and a boolean indicating whether the format was derived from the supported schemas.
        """
        if self.format:
            return self.format, False
        
        if not self.response_schema or not supported_schemas:
            return None, False
        
        return supported_schemas.get(self.response_schema, None), True

# used for token calculation
class ModelDetail(BaseModel):
    llm_model_name: Optional[str] = None
    total_max_tokens: Optional[int] = None
    
class PromptDetail(BaseModel):
    prompt_version: str
    prompt_nickname: str
    llm_model_family: Optional[LLMModelFamily] = LLMModelFamily.AzureOpenAI

class Prompt(BaseModel):
    system_prompt: PromptConfig
    user_prompt: Optional[PromptConfig] = None
    llm_model_parameter: ModelParameter
    llm_model_detail: ModelDetail = ModelDetail()
    prompt_detail: PromptDetail