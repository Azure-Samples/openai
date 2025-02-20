#!/usr/bin/python3
import asyncio
import json
import os
from time import time
from typing import List, Union

from components.models.config_models import SearchSkillConfig, get_valid_config
from components.search.index_manager import SearchIndexManager
from config import DefaultConfig
from quart import Quart, jsonify, request

from common.clients.caching.azure_redis_cache import RedisCachingClient
from common.clients.openai.openai_client import AzureOpenAIClient
from common.clients.services.config_service_client import ConfigServiceClient
from common.contracts.configuration_enum import ConfigurationEnum
from common.contracts.skills.search.api_models import (
    SearchQuery,
    SearchRagResult,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchRetailResult,
    SearchScenario,
)
from common.exceptions import ContentFilterException
from common.telemetry.app_logger import AppLogger, LogEvent
from common.utilities.blob_store import BlobStoreHelper
from components.utils.logging_utils import SearchLoggingEvents
from common.utilities.http_response_utils import HTTPStatusCode, create_error_response

app = Quart(__name__)

DefaultConfig.initialize()
custom_logger = DefaultConfig.custom_logger
logger = AppLogger(custom_logger)
logger.set_base_properties(
    {
        "ApplicationName": "COGNITIVE_SEARCH_SKILL",
    }
)

# Configuration and clients
file_dir = os.path.dirname(os.path.abspath(__file__))

openai_client = AzureOpenAIClient(logger=logger, endpoint=DefaultConfig.AZURE_OPENAI_ENDPOINT, retry=True)
config_service_client = ConfigServiceClient(DefaultConfig.CONFIGURATION_SERVICE_URI, logger)
blob_store_helper = BlobStoreHelper(
    logger=logger,
    storage_account_name=DefaultConfig.AZURE_STORAGE_ACCOUNT_NAME,
    container_name=DefaultConfig.AZURE_STORAGE_IMAGE_CONTAINER,
)

caching_client = RedisCachingClient(
    host=DefaultConfig.REDIS_HOST,
    port=DefaultConfig.REDIS_PORT,
    password=DefaultConfig.REDIS_PASSWORD,
    ssl=False,
    decode_responses=True,
    config_service_client=config_service_client,
)


def get_config(config_name: str) -> SearchSkillConfig:
    config_path = os.path.join(file_dir, "components", "templates", config_name)
    valid_config, config = get_valid_config(config_path=config_path)
    if not valid_config:
        logger.error("Invalid configuration file.")
        raise ValueError("Invalid configuration file. Make sure config file exists and it follows schema format")
    return config


# Initialize default configuration and search manager
default_rag_runtime_config = get_config(config_name="rag.config.json")
default_rag_search_manager = SearchIndexManager(
    default_rag_runtime_config,
    DefaultConfig.AZURE_SEARCH_ENDPOINT,
    openai_client,
    DefaultConfig.AZURE_OPENAI_EMBEDDINGS_ENGINE_NAME,
    logger,
)

default_retail_runtime_config = get_config(config_name="retail.config.json")
default_retail_search_manager = SearchIndexManager(
    default_retail_runtime_config,
    DefaultConfig.AZURE_SEARCH_ENDPOINT,
    openai_client,
    DefaultConfig.AZURE_OPENAI_EMBEDDINGS_ENGINE_NAME,
    logger,
)


async def process_search(
    search_manager: SearchIndexManager,
    query: SearchQuery,
    search_scenario: SearchScenario,
):
    logger.info(f"Search.SearchStart: sid={query.search_id}", SearchLoggingEvents.SEARCH_START)
    start_time = time()

    results = await search_manager.get_product_image_index().search(
        search_query=query,
        results_count=query.max_results_count,
        search_id=query.search_id,
    )

    # 2- verify item limits
    if len(results) > query.max_results_count:
        results = results[: query.max_results_count]

    search_results: List[Union[SearchRagResult, SearchRetailResult]] = []
    for i, item_result in enumerate(results):
        # For some reason this field is not being returned by the search.
        # TODO: Fix this in the future
        if "category" not in item_result:
            item_result["category"] = "N/A"

        if "@search.reranker_score" in item_result:
            item_result["search_score"] = item_result["@search.reranker_score"]
            del item_result["@search.reranker_score"]

        if search_scenario == SearchScenario.RETAIL:
            # Generate SAS Urls for all image results.
            result = SearchRetailResult(**item_result)
            result.imageUrl = await blob_store_helper.generate_blob_sas_url(blob_name=f"{result.articleId}.png")
        else:
            result = SearchRagResult(**item_result)

        search_results.append(result)

    duration = time() - start_time

    logger.info(
        f"Search.SearchSuccess: sid={query.search_id}, originalCount={len(results)}, filteredCount={len(results)}, duration={duration:.4f}s", SearchLoggingEvents.SEARCH_COMPLETE)

    return SearchResult(
        search_query=query.search_query,
        search_id=query.search_id,
        search_results=search_results,
        filter_succeeded=False,
    )


@app.route("/search", methods=["POST"])
async def search():
    logger.log_request_received("Search.PostRequestReceived")

    # 1- validate request input
    request_data = await request.get_json()
    search_request = SearchRequest(**request_data)
    if len(search_request.search_queries) == 0:
        return create_error_response(HTTPStatusCode.BAD_REQUEST, "Must provide at least 1 search_query as input", logger=logger)

    for query in search_request.search_queries:
        if search_request.search_overrides.top:
            query.max_results_count = search_request.search_overrides.top

        if query.min_results_count > query.max_results_count:
            return create_error_response(HTTPStatusCode.BAD_REQUEST, "max_results_count must be greater than min_results_count", logger=logger)

        if query.search_query == "":
            return create_error_response(HTTPStatusCode.BAD_REQUEST, "search_query must not be empty", logger=logger)

    # Extract search scenario from request params
    search_scenario = SearchScenario(request.args.get("scenario", "rag").upper())

    # Initialize search_manager with a default value
    search_manager = None

    # 2- Update search manager with the latest configuration if one passed as an override
    if search_request.search_overrides.config_version:
        config_version = search_request.search_overrides.config_version
        try:
            cached_config = await caching_client.get(ConfigurationEnum.SEARCH_RUNTIME.value, config_version)
            runtime_config = json.loads(cached_config)
            if runtime_config:
                search_config = SearchSkillConfig(**runtime_config)
                logger.info(
                    f"Loaded {ConfigurationEnum.SEARCH_RUNTIME.value}, configuration version: {config_version} from cache."
                )
            else:
                logger.error(
                    f"Failed to fetch configuration id {ConfigurationEnum.SEARCH_RUNTIME.value} configuration version: {config_version}. Will use default search configuration."
                )
                search_config = (
                    default_rag_runtime_config
                    if search_scenario == SearchScenario.RAG
                    else default_retail_runtime_config
                )

            search_manager = SearchIndexManager(
                search_config,
                DefaultConfig.AZURE_SEARCH_ENDPOINT,
                openai_client,
                DefaultConfig.AZURE_OPENAI_EMBEDDINGS_ENGINE_NAME,
                logger,
            )
        except Exception as e:
            logger.error(
                f"Failed to retrieve latest application runtime config. Will use default search config. Exception: {e}"
            )
    if search_manager is None:
        search_manager = (
            default_rag_search_manager if search_scenario == SearchScenario.RAG else default_retail_search_manager
        )

    search_ids_str = ",".join([x.search_id for x in search_request.search_queries])
    logger.info(f"Search BatchProcessing: sids={search_ids_str}", SearchLoggingEvents.SEARCH_BATCH_START)
    search_results: List[SearchResult] = []

    try:
        # 3- Processing multiple search queries using threads
        search_results = await asyncio.gather(
            *(process_search(search_manager, query, search_scenario) for query in search_request.search_queries)
        )
        logger.info(f"Search BatchSuccess: sids={search_ids_str}", SearchLoggingEvents.SEARCH_BATCH_COMPLETE)
    except ContentFilterException as e:
        return create_error_response(logger, HTTPStatusCode.FORBIDDEN, "Content filter exception")
    except ValueError as value_ex:
        return create_error_response(logger, HTTPStatusCode.BAD_REQUEST, f"Bad request. {value_ex}")

    # 4- Remove reference to the same productIds across different search results
    product_key = search_manager.get_product_image_index().get_product_id_field_name()

    seen_ids = set()
    items_deleted = 0
    for i, query_results in enumerate(search_results):
        deletion_indexes = []
        for j, result in enumerate(query_results.search_results):
            pid = result.model_dump().get(product_key)
            if pid not in seen_ids:
                seen_ids.add(pid)
            else:
                deletion_indexes.append(j)

        # to avoid deleting items in place deleting indexes in reverse
        for index in reversed(deletion_indexes):
            search_results[i].search_results.pop(index)
            items_deleted += 1

    # 5- return response
    logger.info(
        f"ImageSearch.BatchSuccess: sids={search_ids_str}, repeated ids deleted={items_deleted}", LogEvent.REQUEST_SUCCESS)

    return jsonify(SearchResponse(results=search_results).to_dict()), 200


@app.route("/health", methods=["GET"])
async def health():
    return {"status": "search skill healthy"}

if __name__ == "__main__":
    host = DefaultConfig.SERVICE_HOST
    port = int(DefaultConfig.SERVICE_PORT)
    app.run(host, port)
