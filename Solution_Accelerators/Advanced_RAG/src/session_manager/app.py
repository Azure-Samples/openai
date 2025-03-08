import asyncio
import json
import mimetypes
import os

import aiohttp_cors
import requests
from aiohttp import web
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from config import DefaultConfig
from handlers.client_manager import ClientManager
from handlers.conversation_handler import ConversationHandler
from handlers.message_queue_handler import MessageQueueHandler
from pydantic import ValidationError
from utils.adaptive_cards import AdaptiveCardConverter
from utils.thread_safe_cache import ThreadSafeCache

from common.clients.caching.azure_redis_cache import RedisCachingClient
from common.clients.services.config_service_client import ConfigServiceClient
from common.clients.services.data_client import DataClient
from common.contracts.configuration_enum import ConfigurationEnum
from common.contracts.orchestrator.bot_response import BotResponse
from common.contracts.session_manager.chat_request import ChatRequest, ResponseMode
from common.contracts.session_manager.scenario import Scenario
from common.contracts.session_manager.session_manager_config_model import (
    SessionManagerConfig,
)
from common.telemetry.app_logger import AppLogger, LogEvent
from common.utilities.files import load_file
from common.utilities.http_response_utils import HTTPStatusCode
from common.utilities.task_manager import TaskManager

routes = web.RouteTableDef()

DefaultConfig.initialize()

# get the logger that is already initialized
custom_logger = DefaultConfig.custom_logger
logger = AppLogger(custom_logger)
logger.set_base_properties(
    {
        "ApplicationName": "SESSION_MANAGER_SERVICE",
    }
)

data_client = DataClient(DefaultConfig.DATA_SERVICE_URI, logger)

chat_request_task_manager = TaskManager(
    logger,
    queue_name=DefaultConfig.SESSION_MANAGER_CHAT_REQUEST_TASK_QUEUE_CHANNEL,
    redis_host=DefaultConfig.REDIS_HOST,
    redis_port=DefaultConfig.REDIS_PORT,
    redis_password=DefaultConfig.REDIS_PASSWORD,
    redis_ssl=False,
)

chat_request_task_manager_retail = TaskManager(
    logger,
    queue_name=DefaultConfig.SESSION_MANAGER_CHAT_REQUEST_TASK_QUEUE_CHANNEL_RETAIL,
    redis_host=DefaultConfig.REDIS_HOST,
    redis_port=DefaultConfig.REDIS_PORT,
    redis_password=DefaultConfig.REDIS_PASSWORD,
    redis_ssl=False,
)

clients = ThreadSafeCache[ClientManager](logger)

chat_response_message_queue = MessageQueueHandler(
    logger=logger,
    redis_host=DefaultConfig.REDIS_HOST,
    redis_port=DefaultConfig.REDIS_PORT,
    redis_password=DefaultConfig.REDIS_PASSWORD,
    redis_ssl=False,
)

chat_response_message_queue_retail = MessageQueueHandler(
    logger=logger,
    redis_host=DefaultConfig.REDIS_HOST,
    redis_port=DefaultConfig.REDIS_PORT,
    redis_password=DefaultConfig.REDIS_PASSWORD,
    redis_ssl=False,
)

adaptive_card_converter = AdaptiveCardConverter(
    load_file(os.path.join("static", "adaptive_card_template.json"), "json"),
    DefaultConfig.SESSION_MANAGER_URI,
)

# Initialize configuration hub client
config_service_client = ConfigServiceClient(DefaultConfig.CONFIGURATION_SERVICE_URI, logger=logger)

caching_client = RedisCachingClient(
    host=DefaultConfig.REDIS_HOST,
    port=DefaultConfig.REDIS_PORT,
    password=DefaultConfig.REDIS_PASSWORD,
    ssl=False,
    decode_responses=True,
    config_service_client=config_service_client,
)


@routes.get("/")
async def health_check(request: web.Request):
    return web.Response(text="Session manager is running!", status=200)


@routes.get("/assets/{rest_of_path}")
async def assets(request: web.Request):
    rest_of_path = request.match_info.get("rest_of_path", None)
    base_path = os.path.join("assets")
    full_path = os.path.normpath(os.path.join(base_path, rest_of_path))
    if not full_path.startswith(base_path):
        raise web.HTTPForbidden(reason="Invalid path")
    return web.FileResponse(full_path)


# Serve content files from blob storage from within the app to keep the example self-contained.
# *** NOTE *** this assumes that the content files are public, or at least that all users of the app
# can access all the files. This is also slow and memory hungry.


@routes.get("/content/{path}")
async def content_file(request: web.Request):
    # Setup logger
    logger = AppLogger(custom_logger)
    base_properties = {"ApplicationName": "SESSION_MANAGER_SERVICE"}
    logger.set_base_properties(base_properties)

    path = request.match_info.get("path", None)
    override_version = request.query.get("override_version", None)
    logger.log_request_received(f"Received request for content: {path} with override version: {override_version}")

    # Retrieve content from Blob store
    try:
        azure_credential = DefaultAzureCredential()

        if override_version:
            override_json = json.loads(
                await caching_client.get(ConfigurationEnum.SESSION_MANAGER_RUNTIME.value, override_version)
            )

            if override_json:
                session_manager_config = SessionManagerConfig(**override_json)
                logger.info(
                    f"Found override configuration {json.dumps(override_json)} for version: {override_version}"
                )
            else:
                logger.error(
                    f"Failed to find override configuration for version: {override_version}. Will use default configuration."
                )
                session_manager_config = None
        else:
            session_manager_config = None

        azure_storage_account = (
            session_manager_config.azure_storage_account
            if session_manager_config and session_manager_config.azure_storage_account
            else DefaultConfig.AZURE_STORAGE_ACCOUNT
        )
        content_container = (
            session_manager_config.azure_storage_container
            if session_manager_config and session_manager_config.azure_storage_container
            else DefaultConfig.AZURE_STORAGE_CONTAINER
        )

        blob_client = BlobServiceClient(
            account_url=f"https://{azure_storage_account}.blob.core.windows.net",
            credential=azure_credential,
        )
        blob_container = blob_client.get_container_client(content_container)

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
            status=HTTPStatusCode.OK.value,
            headers={
                "Content-Type": mime_type,
                "Content-Disposition": f"inline; filename={path}",
            },
        )
    except Exception as ex:
        logger.exception(f"Failed to return requested content: {ex}", event=LogEvent.REQUEST_FAILED)
        return web.json_response({"error": str(ex)}, status=HTTPStatusCode.INTERNAL_SERVER_ERROR.value)


@routes.get("/user-profiles")
async def get_all_user_profiles(request: web.Request):
    logger = AppLogger(custom_logger)
    base_properties = {"ApplicationName": "SESSION_MANAGER_SERVICE", "path": "/user-profiles"}
    logger.set_base_properties(base_properties)
    logger.log_request_received(f"fetching all user profiles")
    data_service_uri = DefaultConfig.DATA_SERVICE_URI
    data_client = DataClient(data_service_uri, logger)

    try:
        user_profiles = data_client.get_all_user_profiles()
        user_profiles_dict = [user_profile.model_dump() for user_profile in user_profiles]
        logger.log_request_success(f"done fetching user profiles")
        return web.json_response(user_profiles_dict)
    except Exception as e:
        logger.exception(f"Exception in /user-profiles: {e}", event=LogEvent.REQUEST_FAILED)
        return web.json_response({"error": str(e)}), HTTPStatusCode.INTERNAL_SERVER_ERROR.value


@routes.delete("/chat-sessions/{user_id}/{conversation_id}")
async def clear_chat_session(request: web.Request):
    user_id = request.match_info.get("user_id", None)
    conversation_id = request.match_info.get("conversation_id", None)

    # initialize logger
    logger = AppLogger(custom_logger)
    base_properties = {
        "ApplicationName": "SESSION_MANAGER_SERVICE",
        "user_id": user_id,
        "conversation_id": conversation_id,
        "path": "/chat-sessions",
    }
    logger.set_base_properties(base_properties)

    data_service_uri = DefaultConfig.DATA_SERVICE_URI
    data_client = DataClient(data_service_uri, logger)

    try:
        data_client.clear_chat_session(user_id, conversation_id)
        logger.log_request_success(f"cleared chat session.")
        return web.json_response({"message": "cleared chat session"}, status=200)
    except Exception as e:
        logger.log_request_failed(f"Exception in /chat-sessions/<user_id>/<conversation_id>: {e}")
        return web.json_response({"error": str(e)}, status=500)


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


@routes.post("/chat")
async def chat(request: web.Request):
    logger = AppLogger(custom_logger)
    base_properties = {"ApplicationName": "SESSION_MANAGER_SERVICE", "path": "/chat"}
    logger.set_base_properties(base_properties)

    try:
        logger.log_request_received("Chat request received.")
        request_json = await request.json()
        chat_request = ChatRequest(**request_json)

        base_properties = {
            "ApplicationName": "SESSION_MANAGER_SERVICE",
            "conversation_id": chat_request.conversation_id,
            "user_id": chat_request.user_id,
            "dialog_id": chat_request.dialog_id,
        }

        logger.set_base_properties(base_properties)

        # Extract scenario from querystring
        scenario = Scenario(request.rel_url.query.get("scenario", "rag"))
        conversation_handler = ConversationHandler(
            logger=AppLogger(custom_logger),
            data_client=data_client,
            adaptive_card_converter=adaptive_card_converter,
            connection_id="",  # TODO: Plumb in connection ID
            task_manager=None,
            max_response_timeout=DefaultConfig.CHAT_MAX_RESPONSE_TIMEOUT_IN_SECONDS,
            scenario=scenario,
        )
        response, status_code = await conversation_handler.handle_chat_message(chat_request)

        # Check if adaptive card response is requested.
        if request_json.get("response_mode", "json") == ResponseMode.AdaptiveCard:
            return web.json_response(
                adaptive_card_converter.to_adaptive_with_citations(response.model_dump()),
                status=status_code,
            )

        return web.json_response(response.model_dump(), status=status_code)
    except json.decoder.JSONDecodeError:
        logger.log_request_failed("Request body must be JSON")
        return web.json_response(
            {"error": "Request body must be JSON"}, status=HTTPStatusCode.UNSUPPORTED_MEDIA_TYPE.value
        )
    except (ValidationError, ValueError) as e:
        logger.log_request_failed(f"Failed to handle chat message: {e}")
        return web.json_response(
            {"error": "Failed to handle the chat message, please verify the attributes and try again."},
            status=HTTPStatusCode.BAD_REQUEST.value,
        )


@routes.get("/ws/chat")
async def ws_chat(request: web.Request):
    logger = AppLogger(custom_logger)
    base_properties = {"ApplicationName": "SESSION_MANAGER_SERVICE", "path": "/ws/chat"}
    logger.set_base_properties(base_properties)
    logger.log_request_received("WebSocket connection request received.")

    connection_id = request.rel_url.query.get("connection_id")
    scenario = request.rel_url.query.get("scenario", "rag")

    base_properties = {
        "ApplicationName": "SESSION_MANAGER_SERVICE",
        "connection_id": connection_id,
        "scenario": scenario,
    }

    logger.set_base_properties(base_properties)

    if not connection_id:
        logger.error("connection_id is required", event=LogEvent.REQUEST_FAILED)
        return web.json_response({"error": "connection_id is required"}, status=400)

    if scenario.lower() == "rag":
        task_manager = chat_request_task_manager
    elif scenario.lower() == "retail":
        task_manager = chat_request_task_manager_retail
    else:
        logger.error("Invalid scenario", event=LogEvent.REQUEST_FAILED)
        return web.json_response({"error": "Invalid scenario"}, status=400)

    client_manager = None
    try:
        # Create new client manager and add it to cache.
        client_manager = ClientManager(
            connection_id=connection_id,
            logger=logger,
            data_client=data_client,
            adaptive_card_converter=adaptive_card_converter,
            task_manager=task_manager,
            max_response_timeout=DefaultConfig.CHAT_MAX_RESPONSE_TIMEOUT_IN_SECONDS,
            scenario=scenario,
        )

        await clients.add_async(connection_id, client_manager)
        return await client_manager.try_accept_connection_async(connection_id=connection_id, client_request=request)
    finally:
        if client_manager:
            await client_manager.close_connection_async(connection_id)
            await clients.remove_async(connection_id)


async def on_chat_message_response(channel: str, message: str):
    if channel == DefaultConfig.SESSION_MANAGER_CHAT_RESPONSE_MESSAGE_QUEUE_CHANNEL:
        scenario = Scenario.RAG
    elif channel == DefaultConfig.SESSION_MANAGER_CHAT_RESPONSE_MESSAGE_QUEUE_CHANNEL_RETAIL:
        scenario = Scenario.RETAIL
    else:
        raise Exception("Incorrect or unknown message channel.")

    if not message:
        raise Exception("Incorrect message payload.")

    client_manager = None
    try:
        logger = AppLogger(custom_logger)

        message_json = json.loads(message)
        bot_response = BotResponse(**message_json)

        base_properties = {
            "ApplicationName": "SESSION_MANAGER_SERVICE",
            "connection_id": bot_response.connection_id,
            "conversation_id": bot_response.conversation_id,
            "user_id": bot_response.user_id,
            "dialog_id": bot_response.dialog_id,
        }
        logger.set_base_properties(base_properties)

        logger.info(f"ConversationHandler: message response received for connection {bot_response.connection_id}.")

        client_manager = await clients.get_async(bot_response.connection_id)
        return await client_manager.handle_chat_response_scenario_specific_async(bot_response, scenario)
    except Exception as ex:
        logger.error(f"Failed to send a response to client for connection {bot_response.connection_id}: {ex}")
        if client_manager:
            await client_manager.close_connection_async(bot_response.connection_id, message="Internal Error.")


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
        chat_response_message_queue.subscribe_async(
            channels=[DefaultConfig.SESSION_MANAGER_CHAT_RESPONSE_MESSAGE_QUEUE_CHANNEL],
            on_message_received=on_chat_message_response,
        )
    )
    asyncio.create_task(
        chat_response_message_queue_retail.subscribe_async(
            channels=[DefaultConfig.SESSION_MANAGER_CHAT_RESPONSE_MESSAGE_QUEUE_CHANNEL_RETAIL],
            on_message_received=on_chat_message_response,
        )
    )

if __name__ == "__main__":
    asyncio.to_thread(start_server(host=DefaultConfig.SERVICE_HOST, port=DefaultConfig.SERVICE_PORT))
