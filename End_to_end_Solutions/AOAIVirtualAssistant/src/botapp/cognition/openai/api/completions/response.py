from enum import Enum
import json

"""
Defines the finish reasons for an Open AI completions response choice.
"""
class OpenAICompletionsFinishReasons(Enum):
    length = "length"
    stop = "stop"

"""
Defines the structure of an Open AI completions response choice.
"""
class OpenAICompletionsResponseChoice:
    def __init__(self, text: str, index: int, finish_reason: str, logprobs: str):
        self.text = text
        self.index = index
        self.finish_reason = finish_reason
        self.logprobs = logprobs

    def get_text_before_stop_tag(self, stoptoken = None):
        return self.text.split(stoptoken)[0] if stoptoken is not None else self.text
    
    def raise_if_not_stopped(self):
        if self.finish_reason != OpenAICompletionsFinishReasons.stop.value:
            raise Exception(f"Open AI completions response choice was not successfully stopped. Returned finish_reason was {self.finish_reason}.")

"""
Defines the structure of an Open AI completions response.
"""
class OpenAICompletionsResponse:
    def __init__(self, id: str, object: str, created: int, model: str, choices: list, usage: dict):
        self.id = id
        self.object = object
        self.created = created
        self.model = model
        self.choices = choices
        self.usage = usage

    def get_first_choice(self) -> OpenAICompletionsResponseChoice:
        first = self.choices[0]
        return OpenAICompletionsResponseChoice(first['text'], first['index'], first['finish_reason'], first['logprobs'])

    """
    Deserializes and returns the given JSON string into an OpenAICompletionsResponse object.
    """
    @staticmethod
    def as_payload(payload: str):
        dct = json.loads(payload)

        if not {'id', 'object', 'created', 'model', 'choices', 'usage'}.issubset(dct.keys()):
            raise Exception("Invalid OpenAICompletionsResponse payload.")
        
        completions_response = OpenAICompletionsResponse(dct['id'], dct['object'], dct['created'], dct['model'], dct['choices'], dct['usage'])
        
        for choice in completions_response.choices:
            if not {'text', 'index', 'finish_reason', 'logprobs'}.issubset(choice.keys()):
                raise Exception("Invalid OpenAICompletionsResponseChoice payload.")
        
        return completions_response