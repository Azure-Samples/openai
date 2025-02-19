from datetime import datetime
import requests
from typing import List

from common.clients.openai.openai_client import AzureOpenAIClient
from common.contracts.data.prompt import Prompt
from error import (
    InvalidArgumentException,
    ImageAnalysisException
)

from openai import RateLimitError
from openai.types.chat.chat_completion import ChatCompletion
from common.exceptions import ContentFilterException, RateLimitException
from common.clients.openai.openai_settings import ChatCompletionsSettings
from common.clients.openai.openai_chat_completions_configuration import OpenAIChatCompletionsConfiguration

from common.telemetry.app_logger import AppLogger
from mimetypes import guess_type

class OpenAiImageDescriber:
    def __init__(
        self,
        openai_client: AzureOpenAIClient,
        logger: AppLogger,
    ) -> str:
        # Setup logger
        self.logger = logger
        self.openai_client = openai_client


    async def analyze_async(
        self,
        analyze_image_prompt: Prompt,
        user_query: str,
        base64_encoded_img: str,
        mime_type: str | None
    ) -> str:
        self.logger.info("Starting Image Analysis..")

        if analyze_image_prompt is None or base64_encoded_img is None:
            self.logger.error("Invalid argument. Exiting.")
            raise InvalidArgumentException("Invalid argument.")
        
        try:
            system_prompt = analyze_image_prompt.system_prompt.template
            user_prompt = analyze_image_prompt.user_prompt.update_template_with_args({"user_query": user_query})
            prompt_messages = self.create_openai_payload(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                image=base64_encoded_img,
                mime_type=mime_type
            )

            openai_configs=[
                OpenAIChatCompletionsConfiguration(
                    user_prompt="",
                    system_prompt=system_prompt, 
                    messages=prompt_messages, 
                    openai_settings=ChatCompletionsSettings(**analyze_image_prompt.llm_model_parameter.model_dump()),
                    prompt_detail=analyze_image_prompt.prompt_detail
                )
            ]
            completion_responses = await self.openai_client.create_chat_completion_async(
                openai_configs=openai_configs
            )

            completion_response = completion_responses[0]
            image_analysis = completion_response.choices[0].message.content
            return image_analysis
        except RateLimitError as rle:
            self.logger.error(f"recommender failed due to rate limits. Status: {rle.code}")
            raise RateLimitException("Recommender failed due to rate limit. Please try again later.")
        except ContentFilterException as cfe:
            self.logger.error(f"Image describer failed due to content filter. Status: {cfe.status_code}")
            raise ContentFilterException("Image describer failed due to content filter. Please try again later.")
        except requests.exceptions.RequestException as re:
            self.logger.error(
                f'Recommendations generation failed due to request error.\n'
                f'Error details: {re.response}')
            raise ImageAnalysisException(f'Recommendations generation failed. Response: {re.response}')
    
    def create_openai_payload(
        self,
        system_prompt: str,
        user_prompt: str,
        image: str,
        mime_type: str | None
    ) -> List[str]:
        messages: List[str] = []
        if mime_type is None:
            mime_type = 'image/png'

        messages.append(
            {
                "role": "system",
                "content": system_prompt
            }
        )

        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                         "text": user_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url":  f"data:{mime_type};base64,{image}"
                        }
                    }
                ],
            }
        )

        return messages