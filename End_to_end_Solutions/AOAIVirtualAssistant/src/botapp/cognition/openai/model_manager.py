from cognition.openai.api.client import OpenAIClient
from cognition.openai.api.completions.request_params import OpenAICompletionsParams
from cognition.openai.prompt import OpenAIPrompt, OpenAIPromptParameterSizeHandlerMethods
from cognition.openai.prompt import OpenAIPrompt
from utilities.yaml_reader import YAMLReader
import tiktoken

"""
Model manager to generate dialog given the Open AI settings and prompt parameters.
"""


class OpenAIModelManager():
    def __init__(self, config_path, model_name, model_settings):
        config = YAMLReader.read_yaml(config_path)

        if not "models" in config:
            raise Exception("Model config does not contain any models.")
        if not model_name in config["models"]:
            raise Exception("Model config does not contain config for model with name " + model_name + ".")
        
        model_config = config["models"][model_name] 
        prompt_config = model_config["prompt"]

        if not "model_params" in model_config:
            raise Exception("Model config for model " + model_name + " does not contain any model params.")
        self.model_params = OpenAICompletionsParams(**model_config["model_params"])

        self.client = OpenAIClient(model_settings)

        if not "body" in prompt_config:
            raise Exception("Model config for model " + model_name + " does not specify a prompt body.")
        placeholders = prompt_config.get("placeholders", list())
        response = prompt_config.get("response", None)
        self.prompt = OpenAIPrompt(prompt_config["body"], placeholders, response)
        self.encoding = tiktoken.get_encoding("gpt2")

    """
    Prompts an Open AI model to generate a greeting given the specified prompt.
    """
    def generate_dialog(self, placeholders: dict):
        # fill out placeholders in prompt and generate text prompt
        text_prompt = self._generate_text_prompt(placeholders)

        print("Text prompt: ", text_prompt)

        # check if parameterized prompt is longer than max_tokens, if so, try to shorten it
        text_prompt_tokenized = self.encoding.encode(text_prompt)
        if len(text_prompt_tokenized) > self.model_params.max_tokens:
            placeholders_shortened = self._attempt_parameter_shortening(placeholders)
            text_prompt = self._generate_text_prompt(placeholders_shortened)
            text_prompt_tokenized = self.encoding.encode(text_prompt)

        # check prompt size again, if still too long, raise exception
        if len(text_prompt_tokenized) > self.model_params.max_tokens:
            raise Exception("Parameterized prompt is too long. Prompt contains " + str(len(text_prompt_tokenized)) + " tokens, but max_tokens is " + str(self.model_params.max_tokens) + ".")

        response_choice = self.client.completions(text_prompt, self.model_params)
        response_choice.raise_if_not_stopped()
        return response_choice.get_text_before_stop_tag(self.prompt.response_params.stop_tag)
    
    def _attempt_parameter_shortening(self, placeholders: dict) -> dict:
        placeholders_shortened = dict()
        for placeholder in placeholders.keys():
            if self.prompt.placeholders[placeholder].size_handler == OpenAIPromptParameterSizeHandlerMethods.truncate:
                if isinstance(placeholders[placeholder], list) and len(placeholders[placeholder]) > self.prompt.placeholders[placeholder].k:
                    placeholders_shortened[placeholder] = placeholders[placeholder][-self.prompt.placeholders[placeholder].k:]
                else:
                    placeholders_shortened[placeholder] = placeholders[placeholder]
        return placeholders_shortened
    
    def _generate_text_prompt(self, placeholders):
        for placeholder in placeholders.keys():
            self.prompt.fill_placeholder(placeholder, placeholders[placeholder])
        return self.prompt.get_text_prompt()