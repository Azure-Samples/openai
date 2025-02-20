from typing import List, Dict
import time
import json

import asyncio
from tenacity import (
    Retrying,
    stop_after_attempt,
    wait_random_exponential,
)

from common.telemetry.app_logger import AppLogger
from common.telemetry.log_classes import AOAICallLog
from common.contracts.data.prompt import LLMModelFamily
from common.clients.openai.openai_chat_completions_configuration import OpenAIChatCompletionsConfiguration
from common.clients.openai.openai_embeddings_configuration import OpenAIEmbeddingsConfiguration

from openai import AzureOpenAI, AsyncAzureOpenAI
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.create_embedding_response import CreateEmbeddingResponse
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

class ContentFilterException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class AzureOpenAIClient:
    __RETRY_STOP_AFTER_ATTEMPT = 5
    __RETRY_MIN_WAIT_TIME_IN_SECONDS = 1
    __RETRY_MAX_WAIT_TIME_IN_SECONDS = 30

    def __init__(self, logger: AppLogger, endpoint: str, api_version: str = "2024-08-01-preview", concurrent_requests: int = 5, retry: bool = False):
        self.__logger = logger
        self.__endpoint = endpoint
        self.__api_version = api_version
        self.__concurrent_requests = concurrent_requests
        self.__retry = Retrying(
                wait=wait_random_exponential(
                    min=self.__RETRY_MIN_WAIT_TIME_IN_SECONDS,
                    max=self.__RETRY_MAX_WAIT_TIME_IN_SECONDS),
                stop=stop_after_attempt(self.__RETRY_STOP_AFTER_ATTEMPT)
            ) if retry else None

    @property
    def endpoint(self):
        return self.__endpoint

    @property
    def api_version(self):
        return self.__api_version

    @property
    def _token_provider(self):
        return get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )

    def is_valid_chat_completions_messages(self, messages: List[Dict[str, str]]) -> bool:
        if not messages:
            return False

        # Checking the first and last roles
        if messages[0]['role'] != 'system' or messages[-1]['role'] != 'user':
            return False

        # Checking the alternating roles between 'user' and 'assistant'
        expected_role = 'user'
        for i in range(1, -1):  # Skipping the first and last items
            if messages[i]['role'] != expected_role:
                return False
            expected_role = 'assistant' if expected_role == 'user' else 'user'

        return True  # The list passes all checks

    def __create_client(self) -> AzureOpenAI:
        return AzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            azure_ad_token_provider=self._token_provider,
        )

    def __create_async_client(self) -> AsyncAzureOpenAI:
        return AsyncAzureOpenAI(
            api_version=self.api_version,
            azure_endpoint=self.endpoint,
            azure_ad_token_provider=self._token_provider,
        )

    def create_embedding(self, openai_configs: List[OpenAIEmbeddingsConfiguration]):
        return asyncio.run(self.create_embedding_async(openai_configs))

    async def create_embedding_async(self, openai_configs: List[OpenAIEmbeddingsConfiguration]):
        client = self.__create_async_client()
        semaphore = asyncio.Semaphore(self.__concurrent_requests)

        async def coroutine(configuration: OpenAIEmbeddingsConfiguration):
            async with semaphore:
                if self.__retry is not None:
                    embedding_response = await self.__retry(self.generate_embedding, client, configuration)
                else:
                    embedding_response = await self.generate_embedding(client, configuration)
            return embedding_response.data[0].embedding

        return await asyncio.gather(*(coroutine(config) for config in openai_configs))

    async def generate_embedding(self, client: AsyncAzureOpenAI, configuration: OpenAIEmbeddingsConfiguration):
        embedding_response: CreateEmbeddingResponse = await client.embeddings.create(
            input=configuration.content,
            model=configuration.embeddings_deployment_name
        )
        return embedding_response

    def create_chat_completion(
        self,
        openai_configs: List[OpenAIChatCompletionsConfiguration]
    ):
        return asyncio.run(self.create_chat_completion_async(openai_configs))

    async def create_chat_completion_async(
        self,
        openai_configs: List[OpenAIChatCompletionsConfiguration],
    ):
        client = self.__create_async_client()
        semaphore = asyncio.Semaphore(self.__concurrent_requests)

        async def coroutine(configuration: OpenAIChatCompletionsConfiguration):
            async with semaphore:
                if not self.is_valid_chat_completions_messages(configuration.messages):
                    raise ValueError("Invalid message list format")

                self.__logger.info(
                    f"Sending request to OpenAI with messages: {configuration.messages}")

                start = time.monotonic()

                if self.__retry is not None:
                    completion = await self.__retry(self.generate_chat_completions, client, configuration)
                else:
                    completion = await self.generate_chat_completions(client, configuration)

                duration_ms = (time.monotonic() - start) * 1000

                log_properties = AOAICallLog(
                    log_message="AOAI Call",
                    prompt_version = configuration.prompt_detail.prompt_version,
                    prompt_nickname = configuration.prompt_detail.prompt_nickname,
                    llm_model_family = configuration.prompt_detail.llm_model_family,
                    user_prompt=configuration.user_prompt,
                    system_prompt=configuration.system_prompt[:7000] + '... <<TRUNCATED>>.' if len(configuration.system_prompt) > 7000 else configuration.system_prompt,
                    message_list=json.dumps(configuration.messages)[:7000] + '... <<TRUNCATED>>.' if len(json.dumps(configuration.messages)) > 7000 else json.dumps(configuration.messages),
                    llm_model_parameters=json.dumps(configuration.openai_settings.to_dict(), default=str),
                    finish_reason=completion.choices[0].finish_reason,
                    llm_response=completion.choices[0].message.content,
                    completion_token_count=completion.usage.completion_tokens,
                    prompt_token_count=completion.usage.prompt_tokens,
                    total_token_count=completion.usage.total_tokens,
                    duration_ms=duration_ms
                )

                self.__logger.info(
                    log_properties.log_message, properties=log_properties.model_dump())

                log_properties.system_prompt = "<<REMOVED>>"
                log_properties.message_list = "<<REMOVED>>"

                self.__logger.info("AOAI Call. System Prompt: " + configuration.system_prompt, properties=log_properties.model_dump())
                self.__logger.info("AOAI Call. Message List: " + json.dumps(configuration.messages), properties=log_properties.model_dump())

                if completion.choices[0].finish_reason == 'content_filter':
                    raise ContentFilterException(
                        'Completion for this request has been blocked by the content filter.')

            return completion

        return await asyncio.gather(*(coroutine(openai_config) for openai_config in openai_configs))

    async def generate_chat_completions(self, client: AsyncAzureOpenAI, configuration: OpenAIChatCompletionsConfiguration):
        if configuration.prompt_detail.llm_model_family == LLMModelFamily.AzureOpenAI:
            completion: ChatCompletion = await client.beta.chat.completions.parse(
                messages=configuration.messages, **configuration.openai_settings.to_dict()
            )
        elif configuration.prompt_detail.llm_model_family == LLMModelFamily.Phi3:
            completion = self.llm_client.complete(
                messages=configuration.messages, **configuration.openai_settings.to_dict()
            )
        else:
            raise ValueError(f"Unknown LLM model family: {configuration.prompt_detail.llm_model_family}")

        return completion

    def get_azure_openai_client(self) -> AzureOpenAI:
        return self.__create_client()