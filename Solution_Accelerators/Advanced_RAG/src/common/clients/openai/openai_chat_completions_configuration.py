from typing import Optional, List, Dict
from common.contracts.data.prompt import PromptDetail
from common.clients.openai.openai_settings import ChatCompletionsSettings

class OpenAIChatCompletionsConfiguration:
    def __init__(self,
                 messages: Optional[List[Dict[str, str]]] = None,
                 user_prompt: Optional[str] = None,
                 system_prompt: Optional[str] = None,
                 openai_settings: Optional[ChatCompletionsSettings] = None,
                 prompt_detail: Optional[PromptDetail] = None):
        if user_prompt is not None:
            self.user_prompt = user_prompt
        if system_prompt is not None:
            self.system_prompt = system_prompt
        if messages is not None:
            self.messages = messages
        if openai_settings is not None:
            self.openai_settings = openai_settings
        if prompt_detail is not None:
            self.prompt_detail = prompt_detail