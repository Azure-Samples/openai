from aiohttp import web
import json
import os
import time
import asyncio

from common.contracts.common.conversation import Dialog, Conversation
from common.contracts.common.user_profile import UserProfile
from common.telemetry.app_logger import AppLogger
from common.telemetry.log_classes import LogProperties
from common.utilities.http_response_utils import HTTPStatusCode
from config import DefaultConfig
from common.clients.cosmosdb.container import CosmosConflictError
from managers.chat_sessions.manager import ChatSessionManager
from managers.entities.manager import EntitiesManager

from azure.identity import DefaultAzureCredential

# initialize config
DefaultConfig.initialize()

# get the logger that is already initialized
custom_logger = DefaultConfig.custom_logger

cosmos_db_endpoint = DefaultConfig.COSMOS_DB_ENDPOINT
cosmos_db_credential = DefaultConfig.COSMOS_DB_KEY if (os.getenv("ENVIRONMENT") is not None and os.getenv("ENVIRONMENT").upper() != "PROD") else DefaultAzureCredential()
cosmos_db_name = DefaultConfig.COSMOS_DB_NAME
cosmos_db_chat_sessions_container_name = DefaultConfig.COSMOS_DB_CHAT_SESSIONS_CONTAINER_NAME
cosmos_db_entities_container_name = DefaultConfig.COSMOS_DB_ENTITIES_CONTAINER_NAME

async def initialize_db_managers():
    global chat_manager, entities_manager
    chat_manager = await ChatSessionManager.create(cosmos_db_endpoint, cosmos_db_credential, cosmos_db_name, cosmos_db_chat_sessions_container_name)
    entities_manager = await EntitiesManager.create(cosmos_db_endpoint, cosmos_db_credential, cosmos_db_name, cosmos_db_entities_container_name)

# @app.route('/chat-sessions/<user_id>/<conversation_id>', methods=['POST'])
async def create_chat_session(request: web.Request) -> web.Response: 
    logger = AppLogger(custom_logger)
    user_id= request.match_info['user_id']
    conversation_id = request.match_info['conversation_id']
    logger.set_base_properties({"ApplicationName": "DATA_SERVICE", "user_id": user_id, "conversation_id": conversation_id, "path": "/chat-sessions"})
    logger.log_request_received("create_chat_session")

    if not request.can_read_body:
        logger.log_request_failed("Request body must be JSON")
        return web.Response(
                text=json.dumps({"error": "Request body must be JSON"}),
                status=HTTPStatusCode.UNSUPPORTED_MEDIA_TYPE.value, content_type="application/json")
    
    data = await request.json()
    conversation = Conversation(**data)

    try:
        start = time.monotonic()
        session = await chat_manager.create_chat_session(user_id, conversation_id, conversation)
        duration_ms = (time.monotonic() - start) * 1000
        
        addl_dim = {"create-chat-sessions[MS]": duration_ms}
        logger.log_request_received(f'create_chat_session: chat session created for user_id {user_id} session_id {conversation_id}', properties=addl_dim)

        return web.Response(text=session.model_dump_json(), status=201, content_type="application/json")
    except CosmosConflictError as e:
        logger.log_request_failed(f"create_chat_session: error: {e}")
        return web.Response(text=str(e), status=409, content_type="application/json")
    except Exception as e:
        logger.log_request_failed(f"create_chat_session: error: {e}")
        return web.Response(text=str(e), status=500, content_type="application/json")
    
# @app.route('/chat-sessions/<user_id>/<conversation_id>', methods=['GET'])
async def get_chat_session(request: web.Request) -> web.Response:        
    user_id = request.match_info.get('user_id')
    conversation_id = request.match_info.get('conversation_id')

    logger = AppLogger(custom_logger)
    logger.set_base_properties({"ApplicationName": "DATA_SERVICE", "user_id": user_id, "conversation_id": conversation_id, "path": "/chat-sessions"})
    logger.log_request_received("get_chat_session")

    try:
        start = time.monotonic()
        session = await chat_manager.get_chat_session(user_id, conversation_id)
        duration_ms = (time.monotonic() - start) * 1000
        addl_dim ={"get_chat_session_duration_ms": duration_ms}

        if session is None:
            logger.info(f"get_chat_session: session with conversation_id {conversation_id} not found", properties=addl_dim)
            return web.Response(text=f"Chat session with conversation_id {conversation_id} not found.", status=404, content_type="application/json")
        else:
            logger.info("get_chat_session: session found", properties=addl_dim)
            return web.Response(text=session.model_dump_json(), status=200, content_type="application/json")
    except Exception as e:
        logger.exception(f"get_chat_session: error: {e}")
        return web.Response(text=str(e), status=500, content_type="application/json")

# @app.route('/check-chat-session/<user_id>/<conversation_id>', methods=['GET'])
async def check_chat_session(request: web.Request) -> web.Response:        
    user_id = request.match_info.get('user_id')
    conversation_id = request.match_info.get('conversation_id')
    
    logger = AppLogger(custom_logger)
    logger.set_base_properties({"ApplicationName": "DATA_SERVICE", "user_id": user_id, "conversation_id": conversation_id, "path": "/check-chat-session"})
    logger.log_request_received("check_chat_session")

    try:
        start = time.monotonic()
        session = await chat_manager.get_chat_session(user_id, conversation_id)
        duration_ms = (time.monotonic() - start) * 1000
        addl_dim= {"check_chat_session_duration_ms": duration_ms}

        if session is None:
            logger.info(f"check_chat_session: session not found for user_id {user_id} and conversation_id {conversation_id}", properties=addl_dim)
            return web.Response(text="false", status=200, content_type="application/json")
        else:
            logger.info(f"check_chat_session: session found for user_id {user_id} and conversation_id {conversation_id}", properties=addl_dim)
            return web.Response(text="true", status=200, content_type="application/json")
    except Exception as e:
        logger.exception(f"check_chat_session: error: {e}")
        return web.Response(text=str(e), status=500, content_type="application/json")

# @app.route('/chat-sessions/<user_id>/<conversation_id>', methods=['PUT'])
async def update_chat_session(request: web.Request) -> web.Response:        
    user_id = request.match_info.get('user_id')
    conversation_id = request.match_info.get('conversation_id')
    logger = AppLogger(custom_logger)
    log_properties = LogProperties(conversation_id=conversation_id, user_id=user_id, application_name="DATA_SERVICE")
    logger.set_base_properties(log_properties)
    logger.log_request_received("update_chat_session")
    
    if not request.can_read_body:
        logger.log_request_failed("Request body must be JSON")
        return web.Response(
            text=json.dumps({"error": "Request body must be JSON"}),
            status=HTTPStatusCode.UNSUPPORTED_MEDIA_TYPE.value, content_type="application/json")

    data = await request.json()
    dialog = Dialog(**data)

    try:
        session = await chat_manager.add_dialog_to_chat_session(user_id, conversation_id, dialog)        
        logger.log_request_success("update_chat_session: session updated", properties=log_properties)

        return web.Response(text=session.model_dump_json(), status=HTTPStatusCode.OK.value, content_type="application/json")
    # except SessionNotFoundError as e:
    #     logger.exception(f"update_chat_session: error: {e}")
    #     return web.Response(text=str(e), status=404, content_type="application/json")
    except Exception as e:
        logger.log_request_failed(f"update_chat_session: error: {e}")
        return web.Response(text=str(e), status=HTTPStatusCode.INTERNAL_SERVER_ERROR.value, content_type="application/json")
    
# @app.route('/chat-sessions/<user_id>/<conversation_id>', methods=['DELETE'])
async def clear_chat_session(request: web.Request) -> web.Response:        
    user_id = request.match_info.get('user_id')
    conversation_id = request.match_info.get('conversation_id')
    
    logger = AppLogger(custom_logger)
    log_properties = LogProperties(conversation_id=conversation_id, user_id=user_id, application_name="DATA_SERVICE")
    logger.set_base_properties(log_properties)
    logger.log_request_received("clear_chat_session", log_properties)

    try:
        await chat_manager.clear_chat_session(user_id, conversation_id)
        logger.log_request_success(f"clear_chat_session: chat session with conversation id {conversation_id} for user {user_id} cleared successfully", properties=log_properties)
        return web.Response(status=HTTPStatusCode.OK.value, content_type="application/json")
    except Exception as e:
        logger.log_request_failed(f"clear_chat_session: error: {e} ", log_properties)
        return web.Response(text=str(e), status=HTTPStatusCode.INTERNAL_SERVER_ERROR.value, content_type="application/json")
    
# @app.route('/user-profiles/<user_id>', methods=['POST'])
async def create_user_profile(request: web.Request) -> web.Response:        
    user_id = request.match_info.get('user_id')
    logger = AppLogger(custom_logger)
    log_properties = LogProperties(user_id=user_id, application_name="DATA_SERVICE")
    logger.set_base_properties(log_properties)
    logger.log_request_received("create_user_profile", log_properties)
    
    if not request.can_read_body:
        logger.log_request_failed("Request body must be JSON", log_properties)
        return web.Response(
            text=json.dumps({"error": "Request body must be JSON"}),
            status=HTTPStatusCode.UNSUPPORTED_MEDIA_TYPE.value, content_type="application/json")

    request_json = await request.get_json()

    try:
        user_profile = await entities_manager.create_user_profile(user_id, UserProfile(id=user_id, **request_json))
        logger.log_request_success(f"create_user_profile: created user profile for user {user_id}", properties=log_properties)
        return web.Response(text=json.dumps(user_profile.model_dump()), status=HTTPStatusCode.CREATED, content_type="application/json")
    except CosmosConflictError as e:
        logger.log_request_failed(f"create_user_profile: error: {e}", log_properties)
        return web.Response(text=str(e), status=HTTPStatusCode.CONFLICT.value, content_type="application/json")
    except Exception as e:
        logger.log_request_failed(f"create_user_profile: error: {e}", log_properties)
        return web.Response(text=str(e), status=HTTPStatusCode.INTERNAL_SERVER_ERROR.value, content_type="application/json")
    
# @app.route('/user-profiles/<user_id>', methods=['GET'])
async def get_user_profile(request: web.Request) -> web.Response:        
    user_id = request.match_info.get('user_id')
    
    logger = AppLogger(custom_logger)
    log_properties = LogProperties(user_id=user_id, application_name="DATA_SERVICE")
    logger.set_base_properties(log_properties)
    logger.log_request_received("get_user_profile", log_properties)

    try:
        user_profile = await entities_manager.get_user_profile(user_id)

        if user_profile is None:
            logger.log_request_failed(f"get_user_profile: user profile with id {user_id} not found", properties=log_properties)
            return web.Response(text=f"User profile with user_id {user_id} not found.", status=HTTPStatusCode.NOT_FOUND.value, content_type="application/json")
        else:
            logger.log_request_success(f"get_user_profile: found user with id {user_id}", properties=log_properties)
            return web.Response(text=json.dumps(user_profile.model_dump()), status=HTTPStatusCode.OK.value, content_type="application/json")
    except Exception as e:
        logger.log_request_failed(f"get_user_profile: error: {e} ", properties=log_properties)
        return web.Response(text=str(e), status=HTTPStatusCode.INTERNAL_SERVER_ERROR.value, content_type="application/json")

# @app.route('/user-profiles', methods=['GET'])
async def get_all_user_profiles(request: web.Request) -> web.Response:
    logger = AppLogger(custom_logger)
    log_properties = LogProperties(application_name="DATA_SERVICE")
    logger.log_request_received("get_all_user_profiles", log_properties)
    try:
        user_profiles = await entities_manager.get_all_user_profiles()
        logger.log_request_success(f"get_all_user_profiles: {len(user_profiles)} user profiles retrieved successfully", properties=log_properties)
        json_user_profiles = [user_profile.model_dump() for user_profile in user_profiles]
        return web.Response(text=json.dumps(json_user_profiles), status=HTTPStatusCode.OK.value, content_type="application/json")
    except Exception as e:
        logger.log_request_failed(f"get_all_user_profiles: error: {e}", log_properties)
        return web.Response(text=str(e), status=HTTPStatusCode.INTERNAL_SERVER_ERROR.value, content_type="application/json")

def set_base_properties(logger: AppLogger, request, user_id: str) -> dict:
    conversation_id = request.headers.get('Conversation_Id', None)
    if conversation_id is None:
        conversation_id = request.headers.get('Conversation-Id', "Conversation-Id NOT SET in the headers")
    
    dialog_id = request.headers.get('Dialog_Id', None)
    if dialog_id is None:
        dialog_id = request.headers.get('Dialog-id', "Dialog-id NOT SET in the headers")
    
    base_properties = {
        "ApplicationName": "DATA_SERVICE",
        "conversation_id": conversation_id,
        "dialog_id": dialog_id,
        "user_id": user_id
    }

    logger.set_base_properties(base_properties)

async def main():
    await initialize_db_managers()
    host = DefaultConfig.SERVICE_HOST
    port = int(DefaultConfig.SERVICE_PORT)
    
    app = web.Application()
    app.router.add_post('/chat-sessions/{user_id}/{conversation_id}', create_chat_session)
    app.router.add_get('/chat-sessions/{user_id}/{conversation_id}', get_chat_session)
    app.router.add_get('/check-chat-session/{user_id}/{conversation_id}', check_chat_session)
    app.router.add_put('/chat-sessions/{user_id}/{conversation_id}', update_chat_session)
    app.router.add_delete('/chat-sessions/{user_id}/{conversation_id}', clear_chat_session)
    app.router.add_post('/user-profiles/{user_id}', create_user_profile)
    app.router.add_get('/user-profiles/{user_id}', get_user_profile)
    app.router.add_get('/user-profiles', get_all_user_profiles)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()
    
    print(f'Server started at http://{host}:{port}')
    
    # Run until interrupted
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print('Shutting down server...')
        await runner.cleanup()
    
if __name__ == '__main__':
    asyncio.run(main())