import os
from enum import Enum
from common.utilities.files import load_file
import openai
import json
from common.telemetry.app_logger import AppLogger
from common.clients.openai.openai_chat_completions_configuration import (
    OpenAIChatCompletionsConfiguration,
)
from common.clients.openai.openai_settings import ChatCompletionsSettings
from common.clients.openai.openai_client import AzureOpenAIClient
from common.contracts.data.prompt import Prompt, PromptDetail


class Classification(Enum):
    VALID = 'Valid'
    CHIT_CHAT = 'Chit-Chat'
    INVALID = 'Invalid'


class StaticClassifier:
    def __init__(self, openai_client: AzureOpenAIClient, logger: AppLogger) -> None:
        self.openai_client = openai_client
        self.logger = logger

    async def classify(self, messages) -> str:
        prompts = load_file(os.path.join(os.path.dirname(__file__), '..', 'static', 'static_orchestrator_prompts_config.yaml'), "yaml")
        classification_prompt = Prompt(**prompts["static_retail_classifier"])
        system_prompt = classification_prompt.system_prompt.template

        classification_messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        classification_messages.extend(messages)

        try:
            completion_responses = await self.openai_client.create_chat_completion_async(
                openai_configs=[
                    OpenAIChatCompletionsConfiguration(
                        user_prompt=messages[-1]["content"],
                        system_prompt=system_prompt,
                        messages=classification_messages, 
                        openai_settings=ChatCompletionsSettings(**classification_prompt.llm_model_parameter.model_dump()),
                        prompt_detail=classification_prompt.prompt_detail
                    )
                ]
            )

            completion_response = completion_responses[0]

            if completion_response.choices[0].finish_reason == 'stop':
                
                classification = json.loads(completion_response.choices[0].message.content)
                if classification["category"] == Classification.VALID.value:
                    return classification["rephrased_query"]
                else:
                    return classification["category"]

            elif completion_response.choices[0].finish_reason == 'length':
                self.logger.error(f"Plan generation failed. Error: {completion_response.choices[0].message.content}")
                raise openai.OpenAIError("Plan generation failed, please try a different query")
            else: # When OpenAI returns null finish reason
                raise openai.OpenAIError("Plan generation failed. please try again later.")

        except openai.BadRequestError as e:
            self.logger.error(f"Azure OpenAI Badrequest error: {e}")
            raise e
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON Decode Error while decoding GPT output: {completion_response.choices[0].message.content}: {e}")
            raise e
        except Exception as e:
            self.logger.error(f"Error while making OpenAI call. Error: {e}")
            raise e