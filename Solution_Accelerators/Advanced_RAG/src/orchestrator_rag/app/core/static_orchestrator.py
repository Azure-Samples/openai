import json
import re
import time
from typing import List

from app.core.final_answer import FinalAnswerGenerator
from app.core.static_user_query_rephraser import StaticUserQueryRephraser
from app.core.utils.basic_merge import basic_merge
from app.utils.request_manager import RequestManager

from common.clients.openai.openai_client import AzureOpenAIClient
from common.clients.services.search_client import SearchClient
from common.contracts.common.overrides import Overrides, SearchOverrides
from common.contracts.common.user_profile import UserProfile
from common.contracts.orchestrator.answer import Answer
from common.contracts.orchestrator.bot_config_model import RAGOrchestratorBotConfig
from common.contracts.orchestrator.bot_response import BotResponse
from common.contracts.skills.search.api_models import (
    SearchQuery,
    SearchRagResult,
    SearchRequest,
    SearchResponse,
)
from common.exceptions import ContentFilterException, RateLimitException
from common.telemetry.app_logger import AppLogger
from common.telemetry.log_classes import StaticOrchestratorLog


class StaticOrchestrator:
    def __init__(
        self,
        rephraser_client: AzureOpenAIClient,
        final_answer_generator_client: AzureOpenAIClient,
        search_client: SearchClient,
        search_overrides: SearchOverrides,
        request_manager: RequestManager,
        logger: AppLogger,
    ) -> None:
        self.static_query_rephraser = StaticUserQueryRephraser(rephraser_client, logger)
        self.final_answer_generator = FinalAnswerGenerator(final_answer_generator_client, logger)
        self.search_client = search_client
        self.search_overrides = search_overrides
        self.request_manager = request_manager
        self.logger = logger

    async def run(
        self,
        connection_id: str,
        user_id: str,
        conversation_id: str,
        dialog_id: str,
        messages: List[dict],
        locale: str,
        runtime_config: RAGOrchestratorBotConfig,
        user_profile: UserProfile = None,
        overrides: Overrides = Overrides(),
    ) -> BotResponse:
        log_properties = StaticOrchestratorLog()
        try:
            final_answer = None
            execution = {}

            # 1. Get rephrased user query
            await self.request_manager.emit_update("Analysing user query and generating search requests")
            start = time.monotonic()
            search_requests = await self.static_query_rephraser.rephrase_user_query(
                messages, runtime_config.static_user_query_rephraser_prompt
            )
            duration_ms = (time.monotonic() - start) * 1000

            log_properties.search_request_generation_duration_ms = duration_ms
            log_properties.search_requests = json.dumps(search_requests)

            search_queries = []
            search_queries_str = []
            for search_request in search_requests:
                query = SearchQuery(search_query=search_request["search_query"], filter=search_request.get("filter"))
                search_queries.append(query)
                search_queries_str.append(search_request["search_query"])

            await self.request_manager.emit_update(f"Searching for: {search_queries_str}")

            # 2 Run Search
            start = time.monotonic()
            search_request: SearchRequest = SearchRequest(
                search_queries=search_queries, search_overrides=self.search_overrides
            )

            search_response: SearchResponse
            search_response, search_response_code = await self.search_client.perform_rag_search(
                search_request=search_request
            )

            if search_response_code == 429:
                raise RateLimitException(f"Search failed with status code {search_response_code}")
            if search_response_code == 403:
                raise ContentFilterException(f"Search failed with status code {search_response_code}")
            if search_response_code != 200:
                raise Exception(f"Search failed with status code {search_response_code}")

            merged_search_results: List[SearchRagResult] = []
            if (
                overrides.orchestrator_runtime is None
                or overrides.orchestrator_runtime.search_results_merge_strategy == "basic"
            ):
                merged_search_results = basic_merge(search_response)
            else:
                raise Exception(
                    f"Search merge strategy {overrides.orchestrator_runtime.search_results_merge_strategy} not supported"
                )

            await self.request_manager.emit_update(f"Search completed with {len(merged_search_results)} results")

            duration_ms = (time.monotonic() - start) * 1000

            log_properties.search_duration_ms = duration_ms
            log_properties.search_response = "<<TRUNCATED>>"
            log_properties.search_response_code = search_response_code

            execution["cognitiveSearchSkill"] = {
                "step_input": search_request.model_dump(),
                "step_output": search_response.model_dump(),
            }

            user_query = messages[-1]["content"]

            # 3 Generate final_answer from search_response
            start = time.monotonic()
            final_answer, trimmed_search_results = await self.final_answer_generator.generate_answer(
                user_query=user_query,
                merged_search_results=merged_search_results,
                messages=messages,
                final_answer_prompt=runtime_config.final_answer_generation_prompt,
            )
            duration_ms = (time.monotonic() - start) * 1000

            log_properties.final_answer_duration_ms = duration_ms
            log_properties.final_answer = final_answer

            # Remove citations from from final answer ( Ex "{test_doc.pdf}")
            speak_answer = re.sub(r"\{[^\}]*\}", "", final_answer)

            # build the data points
            trimmed_merged_data_points = []
            if trimmed_search_results:
                for search_result in trimmed_search_results:
                    trimmed_merged_data_points.append(search_result.to_string())
            else:
                trimmed_merged_data_points.append("No results found")

            answer = Answer(
                answer_string=final_answer,
                data_points=trimmed_merged_data_points,
                steps_execution=execution,
                speak_answer=speak_answer,
                speaker_locale=locale,
            )

            return BotResponse(
                connection_id=connection_id,
                conversation_id=conversation_id,
                dialog_id=dialog_id,
                user_id=user_id,
                answer=answer,
            )
        except (ContentFilterException, RateLimitException) as e:
            self.logger.error(f"Error while running orchestrator. Message: {e.message}.")
            raise e
        except Exception as e:
            self.logger.error(f"Error while running orchestrator: {e}")
            raise e
        finally:
            self.logger.info(log_properties.log_message, properties=log_properties.model_dump())
