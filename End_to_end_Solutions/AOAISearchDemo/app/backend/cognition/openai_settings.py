from typing import Optional

class ChatCompletionsSettings:
    def __init__(self, engine: str, temperature: Optional[float] = None, n: Optional[int] = None, stream: Optional[bool] = None, stop: Optional[str] = None, max_tokens: Optional[int] = None,
            presence_penalty: Optional[float] = None, frequency_penalty: Optional[float] = None, logit_bias: Optional[dict] = None, user: Optional[str] = None):
        self.engine = engine
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

class EmbeddingsSettings:
    def __init__(self, engine: str, user: Optional[str] = None):
        self.engine = engine
        if user is not None:
            self.user = user