from typing import Optional

from common.contracts.data.prompt import ModelResponseFormat

class ChatCompletionsSettings:
    def __init__(self, deployment_name: str, 
                 temperature: Optional[float] = None, 
                 n: Optional[int] = None, 
                 stream: Optional[bool] = None, 
                 stop: Optional[str] = None, 
                 max_tokens: Optional[int] = None,
                 presence_penalty: Optional[float] = None, 
                 frequency_penalty: Optional[float] = None, 
                 logit_bias: Optional[dict] = None, 
                 user: Optional[str] = None, 
                 seed: Optional[int] = None,
                 llm_response_format: Optional[ModelResponseFormat] = None,
                 supported_output_schemas: Optional[dict] = None):
        if deployment_name is not None:
            self.deployment_name = deployment_name
        if temperature is not None:
            self.temperature = temperature
        if n is not None:
            self.n = n
        if stream is not None:
            self.stream = stream
        if stop is not None:
            self.stop = stop
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if presence_penalty is not None:
            self.presence_penalty = presence_penalty
        if frequency_penalty is not None:
            self.frequency_penalty = frequency_penalty
        if logit_bias is not None:
            self.logit_bias = logit_bias
        if user is not None:
            self.user = user
        if llm_response_format is not None:
            self.response_format, self.is_schema = ModelResponseFormat(**llm_response_format).get_response_format(supported_output_schemas)
        if seed is not None:
            self.seed = seed

    def to_dict(self):
        to_return = {}
        if hasattr(self, "deployment_name"):
            to_return["model"] = self.deployment_name
        if hasattr(self, "temperature"):
            to_return["temperature"] = self.temperature
        if hasattr(self, "n"):
            to_return["n"] = self.n
        if hasattr(self, "stream"):
            to_return["stream"] = self.stream
        if hasattr(self, "stop"):
            to_return["stop"] = self.stop
        if hasattr(self, "max_tokens"):
            to_return["max_tokens"] = self.max_tokens
        if hasattr(self, "presence_penalty"):
            to_return["presence_penalty"] = self.presence_penalty
        if hasattr(self, "frequency_penalty"):
            to_return["frequency_penalty"] = self.frequency_penalty
        if hasattr(self, "logit_bias"):
            to_return["logit_bias"] = self.logit_bias
        if hasattr(self, "user"):
            to_return["user"] = self.user
        if hasattr(self, "response_format"):
            to_return["response_format"] = self.response_format
        if hasattr(self, "seed"):
            to_return["seed"] = self.seed
        return to_return
    
class EmbeddingsSettings:
    def __init__(self, deployment_name: str, user: Optional[str] = None):
        self.model = deployment_name
        if user is not None:
            self.user = user