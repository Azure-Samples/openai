import json
from copy import deepcopy
from openai import AzureOpenAI
from utils.prompt_utils import generate_system_prompt
from config import DefaultConfig


class UtteranceBuilder:
    def __init__(self, openai_client, prompt_config, max_history=3) -> None:
        self.openai_client = openai_client
        self.prompt_config = prompt_config
        self.max_history = max_history
    
    def build_history(self, request_response_pairs):
        history = ""
        for pair in request_response_pairs[-self.max_history:]:
            user = pair["request"]
            history += f"{user}\n"
        return history

    def build_utterance(self, request_response_pairs):

        system_prompt = generate_system_prompt(self.prompt_config['generate_utterance'], {"history": self.build_history(request_response_pairs)})

        build_utterance_messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        completion_response = self.openai_client.chat.completions.create(
            messages=build_utterance_messages, 
            **self.prompt_config["generate_utterance"]["openai_settings"]
        )

        final_answer = completion_response.choices[0].message.content

        return final_answer