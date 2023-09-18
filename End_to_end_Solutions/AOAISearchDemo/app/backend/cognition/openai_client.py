import openai
from backend.contracts.error import ContentFilterException
from backend.cognition.openai_settings import ChatCompletionsSettings, EmbeddingsSettings
from typing import Dict, List

class OpenAIClient:
    def __init__(self):
        # Used by the OpenAI SDK
        openai.api_type = "azure"
        openai.api_version = "2023-03-15-preview"

    def chat_completions(self, messages: List[Dict[str, str]], openai_settings: ChatCompletionsSettings, api_base: str, api_key: str):
        openai.api_base = api_base
        openai.api_key = api_key
        completion = openai.ChatCompletion.create(
            **vars(openai_settings),
            messages=messages
        )
        if completion['choices'][0].get('finish_reason', '') == 'content_filter':
            raise ContentFilterException('Completion for this request has been blocked by the content filter.')
        return completion

    def embeddings(self, input: str, openai_settings: EmbeddingsSettings, api_base: str, api_key: str):
        openai.api_base = api_base
        openai.api_key = api_key
        return openai.Embedding.create(
            **vars(openai_settings), 
            input=input
        )