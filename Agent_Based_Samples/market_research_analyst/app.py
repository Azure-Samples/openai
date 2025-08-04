# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
import json
import os

import aiohttp_cors
from aiohttp import web
from config import DefaultConfig
from opentelemetry import trace
from orchestrator.agent_orchestrator import AgentOrchestrator
from redis.asyncio import Redis
from utils.azure_ai_search_util import AzureAISearchHelper

from common.contracts.common.answer import Answer
from common.contracts.common.error import Error
from common.contracts.orchestrator.request import Request
from common.contracts.orchestrator.response import Response
from common.telemetry.trace_context import extract_and_attach_trace_context
from common.utilities.files import load_file
from common.utilities.redis_message_handler import RedisMessageHandler
from common.utilities.runtime_config import get_orchestrator_runtime_config
from common.utilities.thread_safe_cache import ThreadSafeCache

CONFIG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
DEFAULT_RUNTIME_CONFIG = load_file(os.path.join(CONFIG_FILE_PATH, "market_research_analyst_config.yaml"), "yaml")

DefaultConfig.initialize()

tracer_provider = DefaultConfig.tracer_provider
tracer_provider.set_up()
tracer = trace.get_tracer(__name__)

# get the logger that is already initialized
logger = DefaultConfig.logger

# Create route definitions for API endpoints
routes = web.RouteTableDef()

# Redis client for messaging
redis_messaging_client = Redis(
    host=DefaultConfig.REDIS_HOST,
    port=DefaultConfig.REDIS_PORT,
    password=DefaultConfig.REDIS_PASSWORD,
    ssl=False,
    decode_responses=True,
)

azure_ai_search_helper = AzureAISearchHelper(
    logger=logger,
    endpoint=DefaultConfig.AZURE_AI_SEARCH_ENDPOINT,
    index_name=DefaultConfig.AZURE_AI_SEARCH_INDEX_NAME,
    openai_endpoint=DefaultConfig.AZURE_OPENAI_ENDPOINT,
    embeddings_deployment_name=DefaultConfig.AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT_NAME,
    api_version=DefaultConfig.AZURE_OPENAI_API_VERSION,
)

# Thread-safe cache to handle session to orchestrator mapping
orchestrators = ThreadSafeCache[AgentOrchestrator](logger)


# Health check endpoint
@routes.get("/health")
async def health_check(request: web.Request):
    return web.Response(text="OK", status=200)


async def run_agent_orchestration(request_payload: str, message_handler: RedisMessageHandler):
    try:
        request = Request(**request_payload)
    except Exception as e:
        logger.error(f"Failed to parse request data: {e} \n Request payload: {request_payload}")
        error = Error(
            error_str=f"Failed to parse request data: {e} \n Request payload: {request_payload}", retry=False
        )
        response = Response(answer=Answer(is_final=True), error=error)
        await message_handler.send_final_response(response)
        return

    logger.set_base_properties(
        {
            "ApplicationName": "MARKET_RESEARCH_ANALYST_ORCHESTRATOR_SERVICE",
            "session_id": request.session_id,
            "thread_id": request.thread_id,
            "user_id": request.user_id,
        }
    )
    logger.info(f"Received orchestration request: {request_payload} for session: {request.session_id}")

    await message_handler.send_update("Processing your request...", request.dialog_id)

    try:
        # Check if the request is to store reports
        if request.additional_metadata and request.additional_metadata.get("action") == "save":
            await message_handler.send_update("Saving report..", request.dialog_id)

            original_query = request.additional_metadata.get("research_query")
            logger.info(f"Storing report content for report titled {original_query}")

            saved = await azure_ai_search_helper.save_report(
                generated_report=request.message,
                report_level=request.additional_metadata.get("report_level"),
                persona=request.additional_metadata.get("persona"),
            )

            await message_handler.send_final_response(
                Response(
                    session_id=request.session_id,
                    dialog_id=request.dialog_id,
                    user_id=request.user_id,
                    answer=Answer(
                        answer_string=(
                            "Report saved successfully!" if saved else "Failed to save report. Please retry."
                        ),
                        is_final=True,
                        additional_metadata={
                            "action": "save",
                        },
                    ),
                )
            )
        else:
            # Lookup agent orchestrator for given session id
            # If not found, create one just in time
            agent_orchestrator = await orchestrators.get_async(request.session_id)
            if not agent_orchestrator:
                logger.info(f"Agent orchestrator not found for session {request.session_id}. Creating..")

                # Create orchestrator
                orchestrator_runtime_config = await get_orchestrator_runtime_config(
                    default_runtime_config=DEFAULT_RUNTIME_CONFIG,
                    caching_client=redis_messaging_client,
                    request=request,
                    logger=logger,
                )
                logger.info(f"Resolved orchestrator runtime config: {orchestrator_runtime_config}")

                agent_orchestrator = AgentOrchestrator(
                    logger=logger,
                    message_handler=message_handler,
                    configuration=orchestrator_runtime_config,
                    bing_resource_connection_id=DefaultConfig.AZURE_AI_BING_GROUNDING_CONNECTION_NAME,
                )

                # Initialize workflow
                await agent_orchestrator.initialize_agent_workflow(request.thread_id)

                # Add to session cache
                await orchestrators.add_async(request.session_id, agent_orchestrator)
                logger.info(f"Agent orchestrator created successfully for session {request.session_id}")

            # Invoke agent workflow
            response = await agent_orchestrator.start_agent_workflow(request)

            # Search for saved reports and add to response if available. Report comparison is handled separately.
            # This is to avoid unnecessary searches when the user is specifically looking to compare reports.
            if not request.additional_metadata or request.additional_metadata.get("action") != "compare":
                await message_handler.send_update(
                    "Looking through saved reports to find best matches...", request.dialog_id
                )
                saved_reports = await azure_ai_search_helper.search(query=request.message)
                if saved_reports:
                    response.answer.additional_metadata = response.answer.additional_metadata or {}
                    response.answer.additional_metadata["saved_reports"] = saved_reports

            await message_handler.send_final_response(response)
    except Exception as e:
        logger.exception(f"Exception in /run_agent_orchestration: {e}")
        error = Error(error_str="An error occurred. Please retry..", retry=False)
        response = Response(
            session_id=request.session_id,
            dialog_id=request.dialog_id,
            thread_id=request.thread_id,
            user_id=request.user_id,
            answer=Answer(is_final=True),
            error=error,
        )
        await message_handler.send_final_response(response)


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

                session_id = task.get("session_id")
                thread_id = task.get("thread_id")
                user_id = task.get("user_id")
                extract_and_attach_trace_context(task.get("trace_id", {}))
            except Exception as e:
                logger.error(f"Failed to parse task data: {e}")
                continue
            with tracer.start_as_current_span("process_task_at_orchestrator") as span:
                span.set_attribute("session_id", session_id)
                logger.info(f"Received task data: {task_data}")
                message_handler = RedisMessageHandler(
                    session_id=session_id,
                    thread_id=thread_id,
                    user_id=user_id,
                    redis_client=redis_messaging_client,
                    redis_message_queue_channel=DefaultConfig.REDIS_MESSAGE_QUEUE_CHANNEL,
                )
                await run_agent_orchestration(task, message_handler)
        else:
            await asyncio.sleep(1)


async def run_workers():
    await asyncio.gather(*[worker() for _ in range(DefaultConfig.AGENT_ORCHESTRATOR_MAX_CONCURRENCY)])


async def on_startup(app):
    logger.info("Initializing Agent Orchestrator workers..")
    asyncio.create_task(run_workers())


async def on_shutdown(app):
    # Placeholder for shutdown logic - Cleanup, close connections, etc.
    pass


def start_server(host: str, port: int):
    app = web.Application()
    app.add_routes(routes)

    # Configure default CORS settings.
    cors = aiohttp_cors.setup(
        app,
        defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        },
    )

    # Configure CORS on all routes.
    for route in list(app.router.routes()):
        cors.add(route)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Start server
    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    asyncio.run(start_server(host=DefaultConfig.SERVICE_HOST, port=DefaultConfig.SERVICE_PORT))
