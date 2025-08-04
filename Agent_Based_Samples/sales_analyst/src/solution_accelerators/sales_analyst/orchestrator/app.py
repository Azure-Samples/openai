# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
import asyncio
import os

import aiohttp_cors
from aiohttp import web
from redis.asyncio import Redis
from opentelemetry import trace

from agent_orchestrator import AgentOrchestrator

from common.utilities.files import load_file
from common.telemetry.trace_context import extract_and_attach_trace_context
from common.contracts.common.answer import Answer
from common.contracts.common.error import Error
from common.contracts.orchestrator.request import Request
from common.contracts.orchestrator.response import Response
from common.utilities.thread_safe_cache import ThreadSafeCache

from config.default_config import DefaultConfig
from common.utilities.runtime_config import get_orchestrator_runtime_config
from common.utilities.redis_message_handler import RedisMessageHandler
from models.visualization_settings import VisualizationSettings
from models.error import InvalidConsentError

DefaultConfig.initialize()

tracer_provider = DefaultConfig.tracer_provider
tracer_provider.set_up()
tracer = trace.get_tracer(__name__)

logger = DefaultConfig.logger
logger.set_base_properties(
    {
        "ApplicationName": "ORCHESTRATOR_SERVICE",
    }
)

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

# Thread-safe cache to handle session to orchestrator mapping
orchestrators = ThreadSafeCache[AgentOrchestrator](logger)

default_runtime_config = load_file(
    os.path.join(
        os.path.dirname(__file__),
        "static",
        "sales_analyst_config.yaml",
    ),
    "yaml",
)


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

    # Validate request payload
    if not request.session_id or not request.thread_id or not request.user_id or not request.authorization:
        logger.error(f"Invalid request payload: {request_payload}")
        error = Error(error_str="Invalid request payload", retry=False)
        response = Response(answer=Answer(is_final=True), error=error)
        await message_handler.send_final_response(response)
        return

    logger.set_base_properties(
        {
            "ApplicationName": "ORCHESTRATOR_SERVICE",
            "session_id": request.session_id,
            "thread_id": request.thread_id,
            "user_id": request.user_id,
        }
    )
    logger.info(f"Received orchestration request: {request_payload} for session: {request.session_id}")

    try:
        # Lookup agent orchestrator for given session id
        # If not found, create one just in time
        try:
            agent_orchestrator = await orchestrators.get_async(request.session_id)
            logger.info(f"Agent orchestrator found for session {request.session_id}. Reusing existing one..")
        except KeyError:
            logger.info(f"Agent orchestrator not found for session {request.session_id}. Creating new one..")
            agent_orchestrator = None

        if not agent_orchestrator:
            # TODO: Should a new logger be created for each session?
            logger.info(f"Agent orchestrator not found for session {request.session_id}. Creating..")

            # Create orchestrator
            orchestrator_runtime_config = await get_orchestrator_runtime_config(
                default_runtime_config=default_runtime_config,
                caching_client=redis_messaging_client,
                request=request,
                logger=logger,
            )

            logger.debug(f"Resolved orchestrator runtime config: {orchestrator_runtime_config}")
            agent_orchestrator = AgentOrchestrator(
                logger=logger,
                configuration=orchestrator_runtime_config,
                message_handler=message_handler,
                visualization_settings=VisualizationSettings(
                    storage_account_name=DefaultConfig.STORAGE_ACCOUNT_NAME,
                    visualization_data_blob_container=DefaultConfig.VISUALIZATION_DATA_CONTAINER,
                ),
            )

            # Initialize workflow
            await agent_orchestrator.initialize_agent(thread_id=request.thread_id, user_token=request.authorization)

            # Add to cache
            await orchestrators.add_async(request.session_id, agent_orchestrator)
            logger.info(f"Agent orchestrator created successfully for session {request.session_id}")

        # Invoke process
        response = await agent_orchestrator.run_agent(request)
        await message_handler.send_final_response(response)
        logger.info(f"Orchestration completed successfully for session {request.session_id}")
    except InvalidConsentError as e:
        logger.error(f"Invalid consent error in /run_agent_orchestration: {e}")
        error = Error(error_str="consent_required", retry=False, status_code=403)
        response = Response(
            session_id=request.session_id,
            dialog_id=request.dialog_id,
            thread_id=request.thread_id,
            user_id=request.user_id,
            answer=Answer(is_final=True),
            error=error,
        )
        await message_handler.send_final_response(response)
    except Exception as e:
        logger.exception(f"Exception in /run_agent_orchestration: {e}")
        error = Error(error_str=str(e), retry=False)
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
                trace_id = format(span.get_span_context().trace_id, "032x")
                logger.info(f"started session with trace_id: {trace_id}, session_id: {session_id}")
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
