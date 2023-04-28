class OpenAICompletionsParams:
    """
    Defines the body params for an OpenAI completions request.
    """
    def __init__(self, **kwargs):
        self.max_tokens = kwargs.get("max_tokens", 16)
        self.temperature = kwargs.get("temperature", 0.0)
        self.n = kwargs.get("n", 1)
        self.stream = kwargs.get("stream", False)
        self.stop = kwargs.get("stop", None)
        self.presence_penalty = kwargs.get("presence_penalty", 0.0)
        self.frequency_penalty = kwargs.get("frequency_penalty", 0.0)