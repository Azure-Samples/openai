from asyncio import sleep
import os
import json
import requests
from typing import List
from common.telemetry.log_classes import LogProperties
from common.utilities.http_response_utils import HTTPStatusCode, create_error_response
from quart import Quart, jsonify, request

from config import DefaultConfig
from common.contracts.data.prompt import Prompt
from common.exceptions import RateLimitException
from common.clients.openai.openai_client import AzureOpenAIClient
from common.exceptions import (ContentFilterException, RateLimitException)
from error import RecommendationException
from common.contracts.skills.recommender.api_models import RecommenderRequest, RecommenderResponse, RecommenderResult, CategoriesResponse
from recommenders.openaiRecommender import OpenaiRecommender
from common.telemetry.app_logger import AppLogger
from common.utilities.files import load_file

app = Quart(__name__)

prompts = load_file("prompts_config.yaml", "yaml")

DefaultConfig.initialize()
custom_logger = DefaultConfig.custom_logger
logger = AppLogger(custom_logger)
logger.set_base_properties({"ApplicationName": "RECOMMENDER_SKILL"})

openai_recommender = OpenaiRecommender(
    openai_client=AzureOpenAIClient(logger=logger, endpoint=DefaultConfig.AZURE_OPENAI_ENDPOINT, api_version="2024-08-01-preview", retry=True, ),
    logger=logger,
)

@app.route("/recommend", methods=["POST"])
async def recommend():
    logger = AppLogger(custom_logger)
    conversation_id = request.headers.get('conversation_id', "")
    dialog_id = request.headers.get('dialog_id', "")
    user_id = request.headers.get('user_id', "")
    log_properties = LogProperties(conversation_id=conversation_id, dialog_id=dialog_id, user_id=user_id, application_name="RECOMMENDER_SKILL")

    logger.set_base_properties(log_properties)
    logger.log_request_received("Recommender: Request Received.", properties=log_properties)
    
    if not request.is_json:
        return create_error_response(HTTPStatusCode.UNSUPPORTED_MEDIA_TYPE, "Request must be json.", log_properties)
    
    request_json = await request.get_json()
    recommend_request = RecommenderRequest(**request_json)
    #log_properties.request = recommend_request
    if recommend_request.descriptions is not None:
        logger.info(f"Total descriptions in request payload: {len(recommend_request.descriptions)}")

    # Invoke recommendation engine and respond with Pydantic response type.
    recommendations: List[str] = None
    try:
        prompt = Prompt(**prompts["recommender"])
        # Optionally: Update prompt with context of catalog items to generate grounded recommendations.
        recommendations = await openai_recommender.recommend(
            recommendation_query=recommend_request.recommendation_query,
            descriptions=recommend_request.descriptions,
            recommender_prompt=prompt
        )

        if len(recommendations) == 0:
            return create_error_response(HTTPStatusCode.INTERNAL_SERVER_ERROR, "Recommendation generation failed.", log_properties, logger)
        logger.log_request_success("Recommender: Request Successful.", properties=log_properties)
        return RecommenderResponse(result=RecommenderResult(recommendations=recommendations)).model_dump_json(), HTTPStatusCode.OK.value
    except RecommendationException as ex:
        return create_error_response(HTTPStatusCode.BAD_REQUEST, f"Recommender Failed - Recommendation exception. {ex}", logger)
    except ContentFilterException as ex:
        return create_error_response(HTTPStatusCode.FORBIDDEN, f"Recommender Failed - Content filter exception. {ex}", logger)
    except RateLimitException as ex:
        return create_error_response(HTTPStatusCode.TOO_MANY_REQUESTS, f"Recommender Failed - Rate limit exception. {ex}", logger)
    except Exception as ex:
        return create_error_response(HTTPStatusCode.INTERNAL_SERVER_ERROR, f"Recommender Failed. {ex}", log_properties=log_properties, logger=logger)



if __name__ == "__main__":
    host = DefaultConfig.SERVICE_HOST
    port = int(DefaultConfig.SERVICE_PORT)
    app.run(host, port)