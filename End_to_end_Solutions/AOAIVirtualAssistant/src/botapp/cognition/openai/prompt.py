from enum import Enum
from typing import Optional

"""
Defines the possible size handlers for a given prompt parameter.
"""
class OpenAIPromptParameterSizeHandlerMethods(Enum):
    truncate = "truncate"
    none = "none"

class OpenAIPromptSizeHandler():
    def __init__(self, method: OpenAIPromptParameterSizeHandlerMethods = OpenAIPromptParameterSizeHandlerMethods.none, k: int = 1):
        if not method in OpenAIPromptParameterSizeHandlerMethods:
            raise Exception("Invalid placeholder size handler " + method.value + ". Size handler must be one of the following: " + ", ".join([e.value for e in OpenAIPromptParameterSizeHandlerMethods]))
        self.method = method
        if method is OpenAIPromptParameterSizeHandlerMethods.truncate and k < 1:
            raise Exception("Invalid k value for truncate size handler. Must be greater than 0.")
        self.k = k

def is_valid_placeholder_type(value):
        return isinstance(value, str) or (isinstance(value, list) and all(isinstance(elem, str) for elem in value))

class OpenAIPromptPlaceholder():
    def __init__(self, value = None, size_handler: Optional[OpenAIPromptSizeHandler] = None, open_tag: Optional[str] = None, close_tag: Optional[str] = None):
        if value is not None and not is_valid_placeholder_type(value):
            raise Exception("Invalid placeholder value type " + type(value) + ". Value must be a string or a list of strings")
        self.value = value
        self.size_handler = size_handler
        self.open_tag = open_tag
        self.close_tag = close_tag

    def set_value(self, value):
        if not is_valid_placeholder_type(value):
            raise Exception("Invalid placeholder value type " + type(value) + ". Value must be a string or a list of strings")
        
        if self.open_tag is not None or self.close_tag is not None:
            open_tag = self.open_tag if self.open_tag is not None else ""
            close_tag = self.close_tag if self.close_tag is not None else ""
            if isinstance(value, list):
                value[:] = [open_tag + elem + close_tag for elem in value]
            else:
                value = open_tag + value + close_tag
        self.value = value

class OpenAIPromptResponseParams:
    def __init__(self, response: Optional[dict] = None):
        self.stop_tag = response.get("stop_tag", None) if response is not None else None
"""
Defines the structure of an Open AI prompt.

An Open AI prompt has a base body with placeholders that can be replaced with values.
"""
class OpenAIPrompt:
    PLACEHOLDER_KEY_WORDS = ["<LAST_UTTERANCE>", "<FULL_TRANSCRIPT>","<USER_DATA>","<RELEVANT_INFO>","<AUX_INFO>"]

    def __init__(self, prompt_body: str, placeholders: list, response_params: Optional[dict] = None):
        self.prompt_body = prompt_body
        self.placeholders = dict()
        self.response_params = OpenAIPromptResponseParams(response_params)

        for placeholder in placeholders:
            value = placeholder["value"] if not placeholder["value"] in self.PLACEHOLDER_KEY_WORDS else None
            size_handler = placeholder.get("size_handler", None)
            resize_method = size_handler["method"] if size_handler is not None else OpenAIPromptParameterSizeHandlerMethods.none
            k = size_handler.get("k", 1) if size_handler is not None else 1
            open_tag = placeholder.get("open_tag", None)
            close_tag = placeholder.get("close_tag", None)
            self.placeholders[placeholder["key"]] = OpenAIPromptPlaceholder(value, OpenAIPromptSizeHandler(resize_method, k), open_tag, close_tag)

    def get_text_prompt(self) -> str:
        # make sure all placeholders are filled
        if not self.placeholders_filled():
            raise Exception("Unable to generate text prompt: Not all placeholders were filled.")
        
        prompt = self.prompt_body

        for placeholder in self.placeholders.keys():
            if isinstance(self.placeholders[placeholder].value, list):
                prompt = prompt.replace(placeholder, '\n'.join(self.placeholders[placeholder].value))
            else:
                prompt = prompt.replace(placeholder, self.placeholders[placeholder].value)

        return prompt
    
    def fill_placeholder(self, placeholder: str, value):
        self.placeholders[placeholder].set_value(value)

    def placeholders_filled(self) -> bool:
        for placeholderVal in self.placeholders.values():
            if placeholderVal is None:
                return False

        return True