import asyncio
import json
import os
import random
import time

from app.core.static_orchestrator import StaticOrchestrator
from app.utils.messaging_utils import RedisMessagingUtil
from app.utils.request_manager import (
    HTTPRequestManager,
    MessageQueueRequestManager,
    RequestManager,
)
from common.utilities.http_response_utils import HTTPStatusCode
from config import DefaultConfig
from quart import Quart, jsonify, request
from redis.asyncio import Redis

from common.clients.caching.azure_redis_cache import RedisCachingClient
from common.clients.openai.openai_client import AzureOpenAIClient
from common.clients.services.config_service_client import ConfigServiceClient
from common.clients.services.search_client import SearchClient
from common.contracts.common.error import Error
from common.contracts.configuration_enum import ConfigurationEnum
from common.contracts.orchestrator.bot_config_model import RAGOrchestratorBotConfig
from common.contracts.orchestrator.bot_request import BotRequest
from common.contracts.orchestrator.bot_response import Answer, BotResponse
from common.exceptions import (
    ContentFilterException,
    RateLimitException,
    ServiceUnavailableException,
)
from common.telemetry.app_logger import AppLogger, LogEvent
from common.telemetry.log_classes import LogProperties, OrchestratorRunLog
from common.utilities.files import load_file

DefaultConfig.initialize()
app = Quart(__name__)

# get the logger that is already initialized
custom_logger = DefaultConfig.custom_logger
logger = AppLogger(custom_logger)
logger.set_base_properties(
    {
        "ApplicationName": "ORCHESTRATOR_SERVICE",
    }
)

# Configurations for the orchestrator service
# Todo: unify loading of default configuration via redis - update the implementation to generate dynamic default id and version
default_runtime_config = load_file(
    os.path.join(
        os.path.dirname(__file__),
        "app",
        "static",
        "static_orchestrator_prompts_config.yaml",
    ),
    "yaml",
)


# Initialize configuration hub client
config_service_client = ConfigServiceClient(DefaultConfig.CONFIGURATION_SERVICE_URL, logger=logger)

caching_client = RedisCachingClient(
    host=DefaultConfig.REDIS_HOST,
    port=DefaultConfig.REDIS_PORT,
    password=DefaultConfig.REDIS_PASSWORD,
    ssl=False,
    decode_responses=True,
    config_service_client=config_service_client,
)

# Redis client for messaging
redis_messaging_client = Redis(
    host=DefaultConfig.REDIS_HOST,
    port=DefaultConfig.REDIS_PORT,
    password=DefaultConfig.REDIS_PASSWORD,
    ssl=False,
    decode_responses=True,
)

# Initialize configuration hub client
config_service_client = ConfigServiceClient(DefaultConfig.CONFIGURATION_SERVICE_URL, logger=logger)

# Initialize search client
search_client = SearchClient(base_uri=DefaultConfig.SEARCH_SKILL_URL, logger=logger)

# Initialize the update messages to be displayed to the user
update_messages = [
    "Orchestrating user request...",
    "Aggregating relevant information for your request...",
    "Processing your query, please hold on...",
    "Compiling data for your query...",
    "Generating plan to provide accurate results...",
    "Optimizing your request for better performance...",
]


async def get_orchestrator_runtime_config(start_request: BotRequest) -> RAGOrchestratorBotConfig:
    try:
        orchestrator_config = default_runtime_config

        if (
            start_request.overrides.orchestrator_runtime
            and start_request.overrides.orchestrator_runtime.config_version
        ):
            orchestrator_override_json = json.loads(
                await caching_client.get(
                    ConfigurationEnum.ORCHESTRATOR_RUNTIME.value,
                    start_request.overrides.orchestrator_runtime.config_version,
                )
            )
            if orchestrator_override_json:
                orchestrator_config = orchestrator_override_json
                logger.info(
                    f"Found override configuration {json.dumps(orchestrator_override_json)} for version: {start_request.overrides.orchestrator_runtime.config_version}"
                )
            else:
                logger.error(
                    f"Failed to find override configuration for version: {start_request.overrides.orchestrator_runtime.config_version}. Will use default configuration."
                )

        return RAGOrchestratorBotConfig(**orchestrator_config)

    except Exception as e:
        raise Exception(f"Failed to retrieve latest application runtime config: {e}")


async def start(request_data, request_manager: RequestManager):
    """
    Starts the orchestration with the given request data.
    """
    try:
        bot_request = BotRequest(**request_data)
    except Exception as e:
        logger.error(f"Failed to parse request data: {e} \n Request data: {request_data}")
        error = Error(error_str=f"Failed to parse request data: {e} \n Request data: {request_data}", retry=False)
        response = BotResponse(answer=Answer(), error=error)
        await request_manager.emit_final_answer(response)
        return

    update_message = random.choice(update_messages)
    await request_manager.emit_update(update_message)

    logger.set_base_properties(
        {
            "ApplicationName": "ORCHESTRATOR_SERVICE",
            "user_id": bot_request.user_id,
            "conversation_id": bot_request.conversation_id,
            "dialog_id": bot_request.dialog_id,
        }
    )
    logger.info(f"request: {request_data}")

    azure_openai_client_rephraser = AzureOpenAIClient(
        logger=logger, endpoint=DefaultConfig.AZURE_OPENAI_GPT_SERVICE_REPHRASER
    )

    azure_openai_client_final_answer_generator = AzureOpenAIClient(
        logger=logger,
        endpoint=DefaultConfig.AZURE_OPENAI_GPT_SERVICE_FINAL_ANSWER_GENERATOR,
    )

    search_overrides = (
        bot_request.overrides.search_overrides if bot_request.overrides.search_overrides is not None else None
    )

    static_orchestrator = StaticOrchestrator(
        azure_openai_client_rephraser,
        azure_openai_client_final_answer_generator,
        search_client,
        search_overrides,
        request_manager,
        logger,
    )

    try:
        log_properties = OrchestratorRunLog()
        orchestrator_runtime_config = await get_orchestrator_runtime_config(bot_request)
        log_properties.record_duration_ms()
        logger.info("Set Orchestrator runtime configuration", properties=log_properties.model_dump())

        bot_response = await static_orchestrator.run(
            bot_request.connection_id,
            bot_request.user_id,
            bot_request.conversation_id,
            bot_request.dialog_id,
            bot_request.messages,
            bot_request.locale,
            orchestrator_runtime_config,
            bot_request.user_profile,
            bot_request.overrides,
        )
        log_properties = OrchestratorRunLog()
        log_properties.request = bot_request.model_dump_json()
        log_properties.response = (
            "<<TRUNCATED>>"  # start_response.model_dump_json() may be too huge to fit in the log and get dropped
        )
        log_properties.record_duration_ms()
        logger.info(msg=log_properties.log_message, properties=log_properties.model_dump())

        await request_manager.emit_final_answer(bot_response)
    except (ContentFilterException, RateLimitException, ServiceUnavailableException) as e:
        error = Error(error_str=e.message, retry=True)
        response = BotResponse(connection_id=bot_request.connection_id, answer=Answer(), error=error)
        await request_manager.emit_final_answer(response)
    except Exception as e:
        logger.exception(f"Exception in /start: {e}")
        error = Error(error_str=e.message, retry=False)
        response = BotResponse(connection_id=bot_request.connection_id, answer=Answer(), error=error)
        await request_manager.emit_final_answer(response)


async def worker():
    """
    Worker function to process tasks from the Redis task
    queue. Continuously polls the Redis task queue for new tasks and processes them.
    """
    while True:
        task_data = await redis_messaging_client.lpop(DefaultConfig.REDIS_TASK_QUEUE_CHANNEL)
        if task_data:
            try:
                task = json.loads(task_data)

                connection_id = task.get("connection_id")
                dialog_id = task.get("dialog_id")
                conversation_id = task.get("conversation_id")
                user_id = task.get("user_id")
            except Exception as e:
                logger.error(f"Failed to parse task data: {e}")
                continue

            message_queue_request_manager = MessageQueueRequestManager(
                RedisMessagingUtil(
                    connection_id=connection_id,
                    dialog_id=dialog_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    redis_client=redis_messaging_client,
                    redis_message_queue_channel=DefaultConfig.REDIS_MESSAGE_QUEUE_CHANNEL,
                )
            )
            await start(task, message_queue_request_manager)
        else:
            await asyncio.sleep(1)


async def run_workers():
    await asyncio.gather(*[worker() for _ in range(DefaultConfig.ORCHESTRATOR_CONCURRENCY)])


@app.route("/", methods=["GET"])
async def health_check():
    return "Orchestrator service is running"


@app.route("/start", methods=["POST"])
async def start_route():
    log_properties = LogProperties(application_name="ORCHESTRATOR_SERVICE", path="/start")
    logger.log_request_received("Request received", log_properties)
    if not request.is_json:
        response = BotResponse(answer=Answer(), error="Request body must be JSON")
        logger.error("Request body must be JSON", event=LogEvent.REQUEST_FAILED)
        return jsonify(response.to_dict()), HTTPStatusCode.UNSUPPORTED_MEDIA_TYPE.value

    http_request_manager = HTTPRequestManager()
    await start(await request.get_json(), http_request_manager)

    if http_request_manager.final_answer_json['error']:
        logger.log_request_failed(f"Error: {http_request_manager.final_answer_json['error']}")
        return jsonify(http_request_manager.final_answer_json), HTTPStatusCode.INTERNAL_SERVER_ERROR.value
    else:
        logger.log_request_success("Request processed successfully")
        return jsonify(http_request_manager.final_answer_json), HTTPStatusCode.OK.value


@app.before_serving
async def startup():
    asyncio.create_task(run_workers())


if __name__ == "__main__":
    host = DefaultConfig.SERVICE_HOST
    port = int(DefaultConfig.SERVICE_PORT)
    app.run(host, port)
