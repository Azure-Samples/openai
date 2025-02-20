import copy
import openai
import json
from common.contracts.data.prompt import Prompt
from common.contracts.skills.search.api_models import SearchRetailResult
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

    async def generate_answer(self, rephrased_query: str, retail_search_results: List[SearchRetailResult], messages:List[dict], final_answer_prompt: Prompt) -> Tuple[str, List[SearchRetailResult]]:

        self.logger.info(f"Got {len(retail_search_results)} search results from search skill. Generating final answer")

        prompt_helper = PromptHelper(self.logger)

        system_prompt = prompt_helper.generate_retail_system_message(final_answer_prompt, rephrased_query, retail_search_results)

        prompt_messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        if final_answer_prompt.system_prompt.history.include:
            prompt_messages.extend(prompt_helper.get_history_messages(messages, final_answer_prompt.system_prompt.history.length))
        
        user_prompt = prompt_helper.generate_retail_user_message(final_answer_prompt, rephrased_query, retail_search_results)

        prompt_messages.append(
            {
                "role": "user", "content": user_prompt
            })

        try:
            openai_settings=ChatCompletionsSettings(**final_answer_prompt.llm_model_parameter.model_dump())
            completion_responses = await self.openai_client.create_chat_completion_async(
                openai_configs=[
                    OpenAIChatCompletionsConfiguration(
                        system_prompt=system_prompt,
                        user_prompt=messages[-1]['content'],
                        messages=prompt_messages,
                        openai_settings=openai_settings,
                        prompt_detail=final_answer_prompt.prompt_detail
                    )
                ]
            )
            completion_response = completion_responses[0]

            if completion_response.choices[0].finish_reason == 'stop':
                completion_content_dict = json.loads(completion_response.choices[0].message.content)
                final_answer = completion_content_dict['final_answer']
                relevant_product_ids = completion_content_dict['relevant_ids']
                final_answer_reasoning = completion_content_dict['final_answer_reasoning']
                filtering_reasoning = completion_content_dict['filtering_reasoning']

                trimmed_search_results = []
                for result in retail_search_results:
                    if result.id in relevant_product_ids:
                        trimmed_search_results.append(result)
    
            elif completion_response.choices[0].finish_reason == 'length':
                msg = "Failed to generate final answer. Response length exceeded token limit."
                self.logger.error(f"{msg} Response: {completion_response.choices[0].message.content}")
                raise openai.OpenAIError(msg)
            else: # When OpenAI returns null finish reason
                raise openai.OpenAIError("Failed to use search results for generating response. Please try again later.")

            return final_answer, trimmed_search_results, final_answer_reasoning, filtering_reasoning
        except openai.BadRequestError as e:
            self.logger.error(f"Azure OpenAI Badrequest error: {e}")
            raise e
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON Decode Error while decoding GPT output: {completion_response.choices[0].message.content}: {e}")
            raise e
        except Exception as e:
            self.logger.error(f"Error while making OpenAI call. Error: {e}")
            raise e
