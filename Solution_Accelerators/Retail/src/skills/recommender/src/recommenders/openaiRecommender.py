import requests
import logging
from typing import List, Optional
from pydantic import BaseModel
 
from common.clients.openai.openai_chat_completions_configuration import OpenAIChatCompletionsConfiguration
from common.clients.openai.openai_client import AzureOpenAIClient
from common.clients.openai.openai_settings import ChatCompletionsSettings
from common.contracts.data.prompt import Prompt
from common.telemetry.app_logger import AppLogger
from error import InvalidArgumentException, RecommendationException

from openai import RateLimitError
from common.exceptions import (ContentFilterException, RateLimitException)
from utilities.prompt_utils import SUPPORTED_STRUCTURED_OUTPUTS, RecommendationList, Recommendations


class OpenaiRecommender:
    def __init__(
        self,
        openai_client: AzureOpenAIClient,
        logger: AppLogger
    ) -> str:
        # Setup logger
        self.logger = logger

        # Setup OpenAI Client
        self.openai_client = openai_client

    async def recommend(
        self,
        recommendation_query: str,
        recommender_prompt: Prompt,
        descriptions: Optional[List[str]] = None,
    ) -> List[str]:
        self.logger.info("Starting description analysis for recommendation..")

        if recommender_prompt is None:
            self.logger.error("Invalid argument. Exiting.")
            raise InvalidArgumentException("Invalid argument.")

        try:
            # Setup message payload
            system_prompt = recommender_prompt.system_prompt.template
            prompt_arguments = {"recommendation_query": recommendation_query}
            user_prompt = recommender_prompt.user_prompt.update_template_with_args(prompt_arguments)
            payload = self.create_openai_payload(
                recommender_prompt.system_prompt.template,
                user_prompt,
                descriptions
            )

            openai_settings = ChatCompletionsSettings(supported_output_schemas=SUPPORTED_STRUCTURED_OUTPUTS, **recommender_prompt.llm_model_parameter.model_dump())
            openai_configs=[
                OpenAIChatCompletionsConfiguration(
                    user_prompt="",
                    system_prompt=system_prompt, 
                    messages=payload, 
                    openai_settings=openai_settings,
                    prompt_detail=recommender_prompt.prompt_detail
                )
            ]         
            completion_responses = await self.openai_client.create_chat_completion_async(
                openai_configs=openai_configs
            )
            completion_response = completion_responses[0]    
            recommendations = completion_response.choices[0].message.parsed 
            if not openai_settings.is_schema:  
                return recommendations.split("\n")
            return recommendations.get_recommendations()
        except RateLimitError as rle:
                self.logger.error(f"recommender failed due to rate limits. Status: {rle.code}")
                raise RateLimitException("Recommender failed due to rate limit. Please try again later.")
        except ContentFilterException as cfe:
            self.logger.error(f"recommender failed due to content filter. Status: {cfe.status_code}")
            raise ContentFilterException("Recommender failed due to content filter. Please try uploading another image.")
        except requests.exceptions.RequestException as re:
            self.logger.error(
                f'Recommendations generation failed due to request error.\n'
                f'Error details: {re.response}')
            raise RecommendationException(f'Recommendations generation failed. Response: {re.response}')
        except Exception as e:
            self.logger.error(f"Error while making OpenAI call. Error: {e}")
            raise e


    def create_openai_payload(
        self,
        system_prompt: str,
        user_prompt: str,
        descriptions: Optional[List[str]] = None
    ) -> List[str]:
        messages: List[str] = []

        messages.append(
            {
                "role": "system",
                "content": system_prompt
            }
        )

        # Add image descriptions to the request as user prompt if provided.
        if descriptions is not None:
            for i in range(len(descriptions)):
                user_prompt += f'\n{i+1}. {descriptions[i]}.'

        messages.append(
            {
                "role": "user",
                "content": user_prompt
            }
        )

        return messages