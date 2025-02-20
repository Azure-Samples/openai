import json
import re
import time

import openai

from common.clients.openai.openai_chat_completions_configuration import (
    OpenAIChatCompletionsConfiguration,
)
from common.clients.openai.openai_client import AzureOpenAIClient
from common.clients.openai.openai_settings import ChatCompletionsSettings
from common.contracts.data.prompt import Prompt
from common.contracts.skills.search.api_models import (
    Filter,
    FilterType,
    LogicalOperator,
    SearchFilter,
)
from common.telemetry.app_logger import AppLogger
from common.utilities.prompt_utils import PromptHelper


class StaticUserQueryRephraser:
    def __init__(self, openai_client: AzureOpenAIClient, logger: AppLogger) -> None:
        self.openai_client = openai_client
        self.logger = logger

    async def rephrase_user_query(self, messages, rephraser_prompt: Prompt):

        prompt_helper = PromptHelper(self.logger)
        formatted_user_message = prompt_helper.get_user_message_with_history(messages, rephraser_prompt)

        # Get current time in Year-day format
        current_time = time.time()
        current_date_str = time.strftime("%Y-%m-%d", time.gmtime(current_time))

        system_prompt_with_date = rephraser_prompt.system_prompt.update_template_with_args(
            {"current_date": current_date_str}
        )
        prompt_messages = [
            {"role": "system", "content": system_prompt_with_date},
            {"role": "user", "content": formatted_user_message},
        ]

        try:
            openai_settings = ChatCompletionsSettings(**rephraser_prompt.llm_model_parameter.model_dump())
            completion_responses = await self.openai_client.create_chat_completion_async(
                openai_configs=[
                    OpenAIChatCompletionsConfiguration(
                        user_prompt=messages[-1]["content"],
                        system_prompt=system_prompt_with_date,
                        messages=prompt_messages,
                        openai_settings=openai_settings,
                        prompt_detail=rephraser_prompt.prompt_detail,
                    )
                ]
            )

            completion_response = completion_responses[0]

            if completion_response.choices[0].finish_reason == "stop":
                if openai_settings.response_format.get("type") == "text":
                    return completion_response.choices[0].message.content
                else:
                    search_requests = self._create_search_requests(completion_response.choices[0].message.content)
                    return search_requests

            elif completion_response.choices[0].finish_reason == "length":
                msg = "Failed to rephrase user query. Response length exceeded token limit."
                self.logger.error(f"{msg} Response: {completion_response.choices[0].message.content}")
                raise openai.OpenAIError(msg)
            else:  # When OpenAI returns null finish reason
                raise openai.OpenAIError("Failed to rephrase user query. Please try again later.")

        except openai.BadRequestError as e:
            self.logger.error(f"Azure OpenAI Badrequest error: {e}")
            raise e
        except json.JSONDecodeError as e:
            self.logger.error(
                f"JSON Decode Error while decoding GPT output: {completion_response.choices[0].message.content}: {e}"
            )
            raise e
        except Exception as e:
            self.logger.error(f"Error while making OpenAI call. Error: {e}")
            raise e

    def _create_search_requests(self, completion_response: str) -> list[dict]:
        """
        Parse the completion response from OpenAI and return the search requests with filters.

        Args:
            completion_response (str): The completion response from OpenAI.

        Returns:
            List[dict]: The search requests with filters.
        """
        response = json.loads(completion_response)
        search_requests = response["search_requests"]
        for _, search_request in enumerate(response["search_requests"]):
            search_filters = []
            if search_request.get("subsidiary_filter") is not None:
                subsidiary = search_request["subsidiary_filter"]
                subsidiary_filter = SearchFilter(
                    field_name="subsidiary",
                    field_value=subsidiary,
                    filter_type=FilterType.EQUALS,
                )
                search_filters.append(subsidiary_filter)

            if search_request.get("earliest_year_filter") is not None:
                year = str(search_request["earliest_year_filter"])
                if not self.is_valid_year(year):
                    self.logger.error(f"Invalid year parsed from query: {year}. Skipping year filter.")
                    continue

                year_filter = SearchFilter(
                    field_name="reportedYear",
                    field_value=year,
                    filter_type=FilterType.EQUALS,
                )
                search_filters.append(year_filter)

            if len(search_filters) > 0:
                filter_obj = Filter(search_filters=search_filters, logical_operator=LogicalOperator.AND)
                search_request["filter"] = filter_obj.dict()  # Convert Filter object to dictionary
            else:
                search_request["filter"] = None

        return search_requests

    def is_valid_year(self, year: str) -> bool:
        """
        Check if the year is valid.

        Args:
            year (str): The year to check.

        Returns:
            bool: True if the year is valid, False otherwise
        """
        if not year.isdigit():
            self.logger.error(f"Invalid year parsed from query: {year}")
            return False

        is_valid_year_range = 1900 <= int(year) <= 2100
        if not is_valid_year_range:
            self.logger.error(f"Invalid year parsed from query: {year}")
            return False, year

        return True
