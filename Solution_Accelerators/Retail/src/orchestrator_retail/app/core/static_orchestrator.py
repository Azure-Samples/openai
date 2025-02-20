import json
import random
import re
import time
from typing import List

from app.core.final_answer import FinalAnswerGenerator
from app.core.static_classifier import Classification, StaticClassifier
from app.utils.request_manager import RequestManager

from common.clients.openai.openai_client import AzureOpenAIClient
from common.clients.services.image_describer_client import ImageDescriberClient
from common.clients.services.recommender_client import RecommenderClient
from common.clients.services.search_client import SearchClient
from common.contracts.common.overrides import Overrides, SearchOverrides
from common.contracts.common.user_profile import UserProfile
from common.contracts.orchestrator.bot_config_model import RetailOrchestratorBotConfig
from common.contracts.orchestrator.bot_response import Answer, BotResponse
from common.contracts.skills.image_describer.api_models import AnalysisRequest
from common.contracts.skills.recommender.api_models import RecommenderRequest
from common.contracts.skills.search.api_models import SearchQuery, SearchRequest
from common.exceptions import ContentFilterException, RateLimitException
from common.telemetry.app_logger import AppLogger
from common.telemetry.log_classes import MultimodalStaticOrchestratorLog


class StaticOrchestrator:
    def __init__(
        self,
        openai_client: AzureOpenAIClient,
        image_describer_client: ImageDescriberClient,
        recommender_client: RecommenderClient,
        search_client: SearchClient,
        search_overrides: SearchOverrides,
        request_manager: RequestManager,
        logger: AppLogger,
    ) -> None:
        self.openai_client = openai_client
        self.image_describer_client = image_describer_client
        self.recommender_client = recommender_client
        self.search_client = search_client
        self.search_overrides = search_overrides
        self.static_classifier = StaticClassifier(openai_client, logger)
        self.final_answer_generator = FinalAnswerGenerator(openai_client, logger)
        self.request_manager = request_manager
        self.logger = logger

    async def run(
        self,
        connection_id: str,
        user_id: str,
        conversation_id: str,
        dialog_id: str,
        messages,
        locale: str,
        orchestrator_runtime_config: RetailOrchestratorBotConfig,
        user_profile: UserProfile = None,
        overrides: Overrides = Overrides(),
    ) -> BotResponse:
        log_properties = MultimodalStaticOrchestratorLog()
        try:
            final_answer = None
            execution = {}
            # Describe Images
            # TODO: Add image describer inputs and outputs to execution

            start = time.monotonic()
            messages, descriptions = await self._describe_and_replace_images(messages)
            duraiton_ms = (time.monotonic() - start) * 1000

            log_properties.describe_and_replace_images_duration_ms = duraiton_ms
            log_properties.replaced_images_descriptions = descriptions

            # Classify Request

            start = time.monotonic()
            await self.request_manager.emit_update("Analyzing user query")
            classification_result = await self.static_classifier.classify(messages)
            duraiton_ms = (time.monotonic() - start) * 1000

            log_properties.classification_duration_ms = duraiton_ms
            log_properties.classification_result = classification_result
            trimmed_search_results = []

            if classification_result == Classification.CHIT_CHAT.value:
                final_answer = "Hello! I'm a retail assistant. I can help you find products."
            elif classification_result == Classification.INVALID.value:
                final_answer = "I'm sorry, I don't understand. Please ask a question about retail products"
            else:
                # Run Recommender
                recommendation_query = classification_result
                await self.request_manager.emit_update(
                    "Finding recommendations for your query, getting recommendations for: " + recommendation_query
                )

                start = time.monotonic()
                recommender_response, recommender_status_code = await self.recommender_client.recommend(
                    recommender_request=RecommenderRequest(recommendation_query=recommendation_query)
                )
                duration_ms = (time.monotonic() - start) * 1000

                log_properties.recommender_duration_ms = duration_ms
                log_properties.recommender_response = json.dumps(recommender_response.model_dump()) if recommender_response else None
                log_properties.recommender_response_code = recommender_status_code

                if recommender_status_code == 429:
                    raise RateLimitException(f"Recommender failed with status code {recommender_status_code}")
                elif recommender_status_code == 403:
                    raise ContentFilterException(f"Recommender failed with status code {recommender_status_code}")
                elif recommender_status_code != 200:
                    raise Exception(f"Recommender failed with status code {recommender_status_code}")

                recommendations = recommender_response.result.recommendations

                # Check if any recommendations are empty
                recommendations = [recommendation for recommendation in recommendations if recommendation]
                if not recommendations:
                    raise Exception(f"Recommender returned no or empty recommendations")
                # Run Search

                await self.request_manager.emit_update(
                    f"Found recommendations: {recommendations}. Searching for products"
                )

                start = time.monotonic()
                search_queries: List[SearchQuery] = [
                    SearchQuery(search_query=recommendation_query, max_results_count=3)
                    for recommendation_query in recommendations
                ]
                search_request = SearchRequest(search_queries=search_queries, search_overrides=self.search_overrides)
                search_response, search_response_code = await self.search_client.perform_retail_search(search_request)

                if search_response_code == 429:
                    raise RateLimitException(f"Search failed with status code {search_response_code}")
                if search_response_code == 403:
                    raise ContentFilterException(f"Search failed with status code {search_response_code}")
                if search_response_code != 200:
                    raise Exception(f"Search failed with status code {search_response_code}")

                flattened_search_results = []
                for search_results in search_response.results:
                    flattened_search_results.extend(search_results.search_results)

                duration_ms = (time.monotonic() - start) * 1000

                log_properties.search_duration_ms = duration_ms
                log_properties.search_response = (
                    search_response.model_dump()
                )  # this will not log the search response. but since search_response is too big it may cause this log to get dropped. Data drop 400: Telemetry item length must not exceed 65536
                log_properties.search_response_code = search_response_code

                start = time.monotonic()

                final_answer, trimmed_search_results, final_answer_generation_reasoning, filtering_reasoning = (
                    await self.final_answer_generator.generate_answer(
                        recommendation_query,
                        flattened_search_results,
                        messages,
                        orchestrator_runtime_config.static_retail_final_answer_generation,
                    )
                )

                duration_ms = (time.monotonic() - start) * 1000

                log_properties.final_answer = final_answer
                log_properties.final_answer_generation_duration_ms = duration_ms
                log_properties.final_answer_generation_reasoning = final_answer_generation_reasoning
                log_properties.filtering_reasoning = filtering_reasoning
                log_properties.trimmed_search_results = "<<TRUNCATED>>"

                execution["cognitiveSearchSkill"] = {
                    "step_input": search_request.model_dump(),
                    "step_output": search_response.model_dump(),
                    "trimmed_search_results": trimmed_search_results,
                }

            trimmed_merged_data_points = []

            for search_result in trimmed_search_results:
                trimmed_merged_data_points.append(search_result.to_string())

            if len(trimmed_merged_data_points) == 0:
                trimmed_merged_data_points.append("No results found")
                self.logger.info("No search results found!")
            
            self.logger.info(f"Final answer data points: {len(trimmed_merged_data_points)}")

            answer = Answer(
                answer_string=final_answer,
                data_points=trimmed_merged_data_points,
                steps_execution=execution,
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

    async def _describe_and_replace_images(self, messages):
        last_message = messages[-1]
        descriptions = []
        if last_message["role"] == "user":
            pattern = r"<IMAGE-URI:\s*(.+?)>"
            matches = re.findall(pattern, last_message["content"])
            if matches:
                # Extracting the query (text without the image part)
                user_query = re.sub(pattern, "", last_message["content"]).strip()
                candidate_update_messages = [
                    "I see you have attached few images, let me process them image to give you the best insights.",
                    "Reviewing your fashion choices—this won't take long at all.",
                    "I'm on it! Checking out the patterns and colors in your clothing.",
                    "I'll be done in a jiffy, just examining the textures of your attire.",
                ]

                await self.request_manager.emit_update(random.choice(candidate_update_messages))
                analysis_request = AnalysisRequest(images=matches, user_query=user_query)
                analysis_response, status_code = await self.image_describer_client.analyze(analysis_request)
                if status_code == 200:
                    descriptions = [analysis.analysis for analysis in analysis_response.results]

                    for uri, description in zip(matches, descriptions):
                        last_message["content"] = last_message["content"].replace(
                            f"<IMAGE-URI: {uri}>", f"<IMAGE-DESCRIPTION: {description}>"
                        )
                    messages[-1]["content"] = last_message["content"]
                elif status_code == 429:
                    raise RateLimitException(
                        f"Could not analyze the image due to rate limit on Azure OpenAI resources. Please try again in some time."
                    )
                elif status_code == 403:
                    raise ContentFilterException(
                        f"Image analysis failed due to content filtering. Please try to rephrase your question or use another image."
                    )
                else:
                    raise Exception(f"Image describer failed with status code {status_code}")
        return messages, descriptions
