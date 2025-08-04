# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
import json
import mimetypes

import aiohttp_cors
from aiohttp import web
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from azure.ai.projects import AIProjectClient
from opentelemetry import trace
import requests

from common.utilities.task_queue_manager import TaskQueueManager
from common.utilities.message_queue_manager import MessageQueueManager
from common.telemetry.app_logger import AppLogger, LogEvent
from common.utilities.thread_safe_cache import ThreadSafeCache
from common.contracts.orchestrator.response import Response as OrchestratorResponse

from config import DefaultConfig
from handlers.client_manager import ClientManager

routes = web.RouteTableDef()

DefaultConfig.initialize()

tracer_provider = DefaultConfig.tracer_provider
tracer_provider.set_up()
tracer = trace.get_tracer(__name__)
# get the logger that is already initialized
logger = DefaultConfig.logger
logger.set_base_properties(
    {
        "ApplicationName": "SESSION_MANAGER_SERVICE",
    }
)

request_task_manager = TaskQueueManager(
    logger,
    queue_name=DefaultConfig.SESSION_MANAGER_CHAT_REQUEST_TASK_QUEUE_CHANNEL,
    redis_host=DefaultConfig.REDIS_HOST,
    redis_port=DefaultConfig.REDIS_PORT,
    redis_password=DefaultConfig.REDIS_PASSWORD,
    redis_ssl=False,
)

clients = ThreadSafeCache[ClientManager](logger)

response_message_queue = MessageQueueManager(
    logger=logger,
    redis_host=DefaultConfig.REDIS_HOST,
    redis_port=DefaultConfig.REDIS_PORT,
    redis_password=DefaultConfig.REDIS_PASSWORD,
    redis_ssl=False,
)

# AI Foundry Project Client
ai_foundry_project_client = AIProjectClient(
    endpoint=DefaultConfig.AZURE_AI_AGENT_ENDPOINT,
    credential=DefaultAzureCredential(),
)


@routes.get("/")
async def health_check(request: web.Request):
    return web.Response(text="Session manager is running!", status=200)


@routes.get("/get-speech-token")
def get_speech_token(request: web.Request):
    if not DefaultConfig.SPEECH_REGION or not DefaultConfig.SPEECH_KEY:
        return web.json_response(
            {
                "error": "Speech services are not available. If your app requires speech services, please configure session manager"
            },
            status=500,
        )

    url = f"https://{DefaultConfig.SPEECH_REGION}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {"Ocp-Apim-Subscription-Key": DefaultConfig.SPEECH_KEY}
    response = requests.post(url, headers=headers)
    token = response.text
    return web.json_response({"token": token, "region": DefaultConfig.SPEECH_REGION}, status=200)


@routes.get("/content/{path}")
async def content_file(request: web.Request):
    # Setup logger
    logger = DefaultConfig.logger
    base_properties = {"ApplicationName": "SESSION_MANAGER_SERVICE"}
    logger.set_base_properties(base_properties)

    path = request.match_info.get("path", None)
    logger.log_request_received(f"Received request for content: {path}.")

    # Retrieve content from Blob store
    try:
        azure_credential = DefaultAzureCredential()

        blob_client = BlobServiceClient(
            account_url=f"https://{DefaultConfig.AZURE_STORAGE_ACCOUNT}.blob.core.windows.net",
            credential=azure_credential,
        )
        blob_container = blob_client.get_container_client(DefaultConfig.AZURE_STORAGE_CONTAINER)

        # Path is sourcePage which is of type '1676890185_1-56.pdf'
        # We split right before the page number to extract folder name.
        # sourceFile WITHOUT file extension is the blob folder.
        blob_folder = path.rsplit("-", 1)[0]
        blob = blob_container.get_blob_client(f"{blob_folder}/{path}").download_blob()
        logger.info(f"Found requested content in storage: {path}")

        if "csv" in path:
            logger.info("CSV file is requested. Updating mime-type to text/csv")
            mime_type = "text/plain"

            return web.Response(body=blob.readall(), content_type=mime_type)

        mime_type = blob.properties["content_settings"]["content_type"]
        if mime_type == "application/octet-stream":
            mime_type = mimetypes.guess_type(path)[0] or "application/octet-stream"

        logger.log_request_success(f"Returning requested content: {path}")
        return web.Response(
            body=blob.readall(),
            status=200,
            headers={
                "Content-Type": mime_type,
                "Content-Disposition": f"inline; filename={path}",
            },
        )
    except Exception as ex:
        logger.exception(f"Failed to return requested content: {ex}", event=LogEvent.REQUEST_FAILED)
        return web.json_response({"error": str(ex)}, status=500)


@routes.get("/api/query")
async def ws_chat(request: web.Request):
    session_id = request.rel_url.query.get("session_id")
    if not session_id:
        return web.json_response({"error": "session_id is required"}, status=400)

    with tracer.start_as_current_span(f"start_session_for_{session_id}") as span:
        trace_id = format(span.get_span_context().trace_id, "032x")
        print(f"started session with trace_id: {trace_id}, session_id: {session_id}")

        logger = DefaultConfig.logger
        base_properties = {
            "ApplicationName": "SESSION_MANAGER_SERVICE",
            "path": "/api/query",
            "session_id": session_id,
        }
        logger.set_base_properties(base_properties)

        logger.log_request_received(f"Request received for session {session_id}.")

        client_manager = None
        try:
            # Create new client manager and add it to cache.
            client_manager = ClientManager(
                session_id=session_id,
                logger=logger,
                ai_foundry_project_client=ai_foundry_project_client,
                task_manager=request_task_manager,
                max_response_timeout=DefaultConfig.CHAT_MAX_RESPONSE_TIMEOUT_IN_SECONDS,
            )

            await clients.add_async(session_id, client_manager)
            return await client_manager.try_accept_connection_async(session_id=session_id, client_request=request)
        finally:
            if client_manager:
                await client_manager.close_connection_async(session_id)
                await clients.remove_async(session_id)


async def on_chat_message_response(message: str):
    if not message:
        raise Exception("Incorrect message payload.")

    client_manager = None
    try:
        logger = DefaultConfig.logger

        message_json = json.loads(message)
        orchestrator_response = OrchestratorResponse(**message_json)

        base_properties = {
            "ApplicationName": "SESSION_MANAGER_SERVICE",
            "session_id": orchestrator_response.session_id,
            "thread_id": orchestrator_response.thread_id,
            "user_id": orchestrator_response.user_id,
        }
        logger.set_base_properties(base_properties)

        logger.info(
            f"ConversationHandler: message response received for connection {orchestrator_response.session_id}."
        )

        client_manager = await clients.get_async(orchestrator_response.session_id)
        return await client_manager.handle_chat_response_async(orchestrator_response)
    except Exception as ex:
        logger.error(f"Failed to send a response to client for connection {orchestrator_response.session_id}: {ex}")
        if client_manager:
            await client_manager.close_connection_async(orchestrator_response.session_id, message="Internal Error.")


def start_server(host: str, port: int):
    app = web.Application(logger=logger)
    app.add_routes(routes)

    app.on_startup.append(on_startup)

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

    # Start server
    web.run_app(app, host=host, port=port)


async def on_startup(app):
    asyncio.create_task(
        response_message_queue.subscribe_async(
            channels=[DefaultConfig.SESSION_MANAGER_CHAT_RESPONSE_MESSAGE_QUEUE_CHANNEL],
            on_message_received=on_chat_message_response,
        )
    )


if __name__ == "__main__":
    asyncio.to_thread(start_server(host=DefaultConfig.SERVICE_HOST, port=DefaultConfig.SERVICE_PORT))
