import copy
import openai
import json
from common.contracts.data.prompt import Prompt
from common.contracts.skills.search.api_models import SearchResponse, SearchRagResult
from common.telemetry.app_logger import AppLogger
from common.clients.openai.openai_settings import ChatCompletionsSettings
from common.clients.openai.openai_chat_completions_configuration import OpenAIChatCompletionsConfiguration
from common.clients.openai.openai_client import AzureOpenAIClient
from common.utilities.prompt_utils import PromptHelper
from typing import List, Tuple

class FinalAnswerGenerator:
    def __init__(self, openai_client: AzureOpenAIClient, logger: AppLogger) -> None:
        self.openai_client = openai_client
        self.logger = logger

    async def generate_answer(self, user_query: str, merged_search_results: List[SearchRagResult], messages:List[dict], final_answer_prompt: Prompt) -> Tuple[str, List[SearchRagResult]]:

        self.logger.info(f"Got {len(merged_search_results)} search results from search skill. Generating final answer")

        prompt_helper = PromptHelper(self.logger)
        total_max_token = final_answer_prompt.llm_model_detail.total_max_tokens - final_answer_prompt.llm_model_parameter.max_tokens - 400 #400 tokens for system prompt template

        merged_search_results_copy = copy.deepcopy(merged_search_results)
        trimmed_search_results = prompt_helper.get_trimmed_search_results(search_results=merged_search_results_copy,
                                                                           max_token_length=total_max_token,
                                                                           model_name=final_answer_prompt.llm_model_detail.llm_model_name,
                                                                           messages=messages,
                                                                           history_settings=final_answer_prompt.system_prompt.history)

        system_prompt = prompt_helper.generate_system_message(final_answer_prompt, trimmed_search_results)
        user_prompt = prompt_helper.generate_user_message(final_answer_prompt, trimmed_search_results, user_query)

        prompt_messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        if final_answer_prompt.system_prompt.history.include:
            prompt_messages.extend(prompt_helper.get_history_messages(messages, final_answer_prompt.system_prompt.history.length))

        prompt_messages.extend([
            {
                "role": "user",
                "content": user_prompt
            }
        ])

        try:
            completion_responses = await self.openai_client.create_chat_completion_async(
                openai_configs=[
                    OpenAIChatCompletionsConfiguration(
                        user_prompt=user_query,
                        system_prompt=system_prompt,
                        messages=prompt_messages,
                        openai_settings=ChatCompletionsSettings(**final_answer_prompt.llm_model_parameter.model_dump()),
                        prompt_detail=final_answer_prompt.prompt_detail
                    )
                ]
            )
            completion_response = completion_responses[0]

            if completion_response.choices[0].finish_reason == 'stop':
                final_answer = completion_response.choices[0].message.content
            elif completion_response.choices[0].finish_reason == 'length':
                msg = "Failed to generate final answer. Response length exceeded token limit."
                self.logger.error(f"{msg} Response: {completion_response.choices[0].message.content}")
                raise openai.OpenAIError(msg)
            else: # When OpenAI returns null finish reason
                raise openai.OpenAIError("Failed to use search results for generating response. Please try again later.")

            return final_answer, trimmed_search_results
        except openai.BadRequestError as e:
            self.logger.error(f"Azure OpenAI Badrequest error: {e}")
            raise e
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON Decode Error while decoding GPT output: {completion_response.choices[0].message.content}: {e}")
            raise e
        except Exception as e:
            self.logger.error(f"Error while making OpenAI call. Error: {e}")
            raise e
