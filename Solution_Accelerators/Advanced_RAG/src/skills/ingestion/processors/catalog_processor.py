import asyncio
import base64
import json
import uuid
from typing import Dict, List, Optional

import openai
from clients.azure_storage_client import AzureStorageClient
from indexers.indexer import Indexer
from models.models import CatalogIndexerRequestPayload, CatalogItem

from common.clients.openai.openai_chat_completions_configuration import (
    OpenAIChatCompletionsConfiguration,
)
from common.clients.openai.openai_client import AzureOpenAIClient
from common.clients.openai.openai_embeddings_configuration import (
    OpenAIEmbeddingsConfiguration,
)
from common.clients.openai.openai_settings import ChatCompletionsSettings
from common.contracts.data.prompt import Prompt
from common.telemetry.app_logger import AppLogger

from common.clients.openai.openai_chat_completions_configuration import OpenAIChatCompletionsConfiguration
from common.clients.openai.openai_embeddings_configuration import OpenAIEmbeddingsConfiguration
from managers.task_status_manager import TaskStatusManager, TaskStatus

class CatalogProcessor:
    def __init__(self,
                 logger: AppLogger,
                 detailed_description_prompt: Prompt,
                 summarized_description_prompt: Prompt,
                 storage_client: AzureStorageClient,
                 search_endpoint: str,
                 azure_openai_endpoint: str,
                 azure_openai_embeddings_engine_name: str,
                 catalog_indexer_status_manager: TaskStatusManager
    ) -> None:
        self.logger = logger
        self.detailed_description_prompt = detailed_description_prompt
        self.summarized_description_prompt = summarized_description_prompt
        self.storage_client = storage_client
        self.search_endpoint = search_endpoint
        self.openai_client = AzureOpenAIClient(logger=logger, endpoint=azure_openai_endpoint, retry=True)

        self.embeddings_deployment_name = azure_openai_embeddings_engine_name

        self.catalog_indexer_status_manager = catalog_indexer_status_manager

        self._chunking_lock = asyncio.Lock()

    async def process_async(self, message: bytes):
        payload = CatalogIndexerRequestPayload(**json.loads(message))
        self.logger.info(f"Task {payload.task_id}: Catalog Indexer: Task payload received. Total items: {len(payload.items)}")
        await self.catalog_indexer_status_manager.set_task_status(payload.task_id, "Task is processing by catalog processor.", TaskStatus.PROCESSING)

        chunks: List[Dict] = []
        try:
            for item_idx, catalog_item in enumerate(payload.items, start=1):
                # Step 1: Get image from storage
                image_bytes, image_url = await self.storage_client.download_file_async(
                    payload.images_storage_container,
                    f"{catalog_item.article_id}.png"
                )

                # If image could not be downloaded, skip and move to next item.
                if not image_bytes:
                    continue

                # Step 2: Apply enrichment if requested
                detailed_description = await self.generate_enhanced_description(payload, catalog_item, self.detailed_description_prompt, image_bytes)
                summarized_description = await self.generate_enhanced_description(payload, catalog_item, self.summarized_description_prompt)

                # Step 3: Generate chunk following the index schema
                generated_chunk = await self.generate_chunk_async(catalog_item, detailed_description, summarized_description, image_url)
                chunks.append(generated_chunk)

                self.logger.info(f"Task {payload.task_id}. Chunk generated for {catalog_item.article_id}. Items processed: {item_idx}/{len(payload.items)}")

            # Step 4: Upload chunks in search index.
            indexer = Indexer(search_endpoint=self.search_endpoint, index_name=payload.index_name, logger=self.logger)
            result = await indexer.index_async(chunks, payload.task_id)
            if not result:
                self.logger.error(f"Task {payload.task_id}: Catalog indexing failed. Exiting.")
                return

            self.logger.info(f"Task {payload.task_id}: Catalog Indexed successfully. Total items: {len(payload.items)}")
            await self.catalog_indexer_status_manager.set_task_status(payload.task_id, "Task processed by catalog processor.", TaskStatus.PROCESSED)
        except Exception as ex:
            await self.catalog_indexer_status_manager.set_task_status(payload.task_id, f"An error occured while processing task: {ex}", TaskStatus.FAILED)
            self.logger.exception(f"Task {payload.task_id}: Catalog Indexer failed. {ex}")
            raise

    async def generate_chunk_async(self, item: CatalogItem, detailed_description: str, summarized_description: str, image_url: str) -> Dict:
        chunk = {
            "id": f"{item.article_id}-{uuid.uuid4()}",
            "articleId": item.article_id,
            "productName": item.product_name,
            "productType": item.product_type,
            "indexGroupName": item.index_group_name,
            "gender": item.gender,
            "detailDescription": item.detail_description,
            "detailDescriptionVector": (await self.openai_client.create_embedding_async(
                openai_configs=[
                    OpenAIEmbeddingsConfiguration(
                        content=item.detail_description,
                        embeddings_deployment_name=self.embeddings_deployment_name
                    )
                ]
            ))[0],
            "imageUrl": image_url
        }

        if detailed_description:
            chunk.update({"generatedDescription": detailed_description})
            generated_description_embedding = (await self.openai_client.create_embedding_async(
                openai_configs=[
                    OpenAIEmbeddingsConfiguration(
                        content=detailed_description,
                        embeddings_deployment_name=self.embeddings_deployment_name
                    )
                ]
            ))[0]

            chunk.update({"generatedDescriptionVector": generated_description_embedding})

        if summarized_description:
            chunk.update({"summarizedDescription": summarized_description})
            summarized_description_embedding = (await self.openai_client.create_embedding_async(
                openai_configs=[
                    OpenAIEmbeddingsConfiguration(
                        content=summarized_description,
                        embeddings_deployment_name=self.embeddings_deployment_name
                    )
                ]
            ))[0]

            chunk.update({"summarizedDescriptionVector": summarized_description_embedding})

        return chunk

    async def generate_enhanced_description(self, payload: CatalogIndexerRequestPayload, item: CatalogItem, prompt: Prompt, image: Optional[bytes] = None) -> Optional[str]:
        if not payload.enrichment:
            return None

        self.logger.info(f"Task {payload.task_id}: Catalog Indexer: Generating enhanced description for {item.article_id}")

        prompt_messages = [
            {
                "role": "system",
                "content": prompt.system_prompt.template
            }
        ]

        if image:
            image_as_base64 = base64.b64encode(image).decode('utf-8')
            prompt_messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url":  f"data:image/png;base64,{image_as_base64}"
                            }
                        }
                    ],
                }
            )
        else:
            prompt_messages.append(
                {
                    "role": "user",
                    "content": item.detail_description
                }
            )

        try:
            completion_responses = await self.openai_client.create_chat_completion_async(openai_configs=[
                OpenAIChatCompletionsConfiguration(
                    user_prompt="",
                    system_prompt=prompt.system_prompt.template,
                    messages=prompt_messages,
                    openai_settings=ChatCompletionsSettings(**prompt.llm_model_parameter.model_dump()),
                    prompt_detail=prompt.prompt_detail
                ),
            ]
            )

            if not completion_responses:
                raise openai.OpenAIError("No completion responses received.")

            completion_response = completion_responses[0]
            if completion_response.choices[0].finish_reason == 'stop':
                return completion_response.choices[0].message.content
            else: # When OpenAI returns null finish reason
                raise openai.OpenAIError("Failed to generate detailed description.")
        except openai.BadRequestError as e:
            self.logger.error(f"Azure OpenAI Badrequest error: {e}")
            raise e
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON Decode Error while decoding GPT output: {completion_response.choices[0].message.content}: {e}")
            raise e
        except Exception as e:
            self.logger.error(f"Error while making OpenAI call. Error: {e}")
            raise e