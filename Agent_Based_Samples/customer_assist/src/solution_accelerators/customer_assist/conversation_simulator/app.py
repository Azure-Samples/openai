# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

# filepath: c:\Users\manniarora\dev\cxe-eng\agents\src\solution_accelerators\customer_assist\conversation_simulator\api.py
# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
import uuid
from typing import Dict
import aiohttp_cors
from aiohttp import web
from config.default_config import DefaultConfig
from conversation_simulator import ConversationSimulator

DefaultConfig.initialize()
logger = DefaultConfig.custom_logger

# Initialize thread-safe session cache with lock
conversation_sessions: Dict[str, ConversationSimulator] = {}
sessions_lock = asyncio.Lock()  # Lock for thread-safe access to conversation_sessions

# Create route definitions for API endpoints
routes = web.RouteTableDef()


@routes.get("/status")
async def status(request):
    """Status endpoint to check if the service is running."""
    async with sessions_lock:
        active_sessions = len(conversation_sessions)
    return web.json_response({"status": "running", "active_sessions": active_sessions})


@routes.post("/start")
async def start_conversation(request: web.Request):
    """Start a new conversation simulation."""
    # Get session_id from request or generate a new one
    data = await request.json() if request.can_read_body else {}
    session_id = data.get("session_id", str(uuid.uuid4()))

    # Check if session already exists using the lock
    async with sessions_lock:
        if session_id in conversation_sessions:
            return web.json_response(
                {"success": False, "error": f"Session {session_id} already exists"},
                status=409,  # Conflict
            )

    try:
        # Create new conversation simulator
        simulator = ConversationSimulator(
            session_id=session_id,
            logger=logger,
        )

        # Start the conversation
        success = await simulator.start()

        if success:
            # Store in session cache
            async with sessions_lock:
                conversation_sessions[session_id] = simulator

            return web.json_response(
                {
                    "success": True,
                    "session_id": session_id,
                    "message": f"Conversation started with session ID: {session_id}",
                },
                status=201,  # Created
            )
        else:
            return web.json_response(
                {"success": False, "error": "Failed to start conversation"}, status=500
            )  # Internal Server Error

    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        return web.json_response(
            {"success": False, "error": str(e)}, status=500
        )  # Internal Server Error


@routes.get("/next")
async def get_next_message(request: web.Request):
    """Get the next message from a conversation."""
    # Get session_id from query parameters
    session_id = request.query.get("session_id")

    if not session_id:
        return web.json_response(
            {"success": False, "error": "session_id is required"}, status=400
        )  # Bad Request

    # Check if session exists with proper locking
    async with sessions_lock:
        if session_id not in conversation_sessions:
            return web.json_response(
                {"success": False, "error": f"Session {session_id} not found"},
                status=404,
            )  # Not Found
        simulator = conversation_sessions[session_id]

    # Check if simulator is running
    if not simulator.is_running:
        return web.json_response(
            {
                "success": False,
                "error": "Conversation has ended or stopped",
                "is_running": False,
            },
            status=400,  # Bad Request
        )

    # Get next message
    message = await simulator.get_next_message()

    if message is None:
        # Conversation has ended
        return web.json_response(
            {
                "success": True,
                "session_id": session_id,
                "message": None,
                "is_running": False,
            },
            status=200,
        )

    return web.json_response(
        {
            "success": True,
            "session_id": session_id,
            "message": message.to_dict(),
            "is_running": simulator.is_running,
        },
        status=200,
    )


@routes.post("/stop")
async def stop_conversation(request: web.Request):
    """Stop a conversation simulation."""
    # Get session_id from request
    data = await request.json() if request.can_read_body else {}
    session_id = data.get("session_id")

    if not session_id:
        return web.json_response(
            {"success": False, "error": "session_id is required"}, status=400
        )  # Bad Request

    # Check if session exists with proper locking
    async with sessions_lock:
        if session_id not in conversation_sessions:
            return web.json_response(
                {"success": False, "error": f"Session {session_id} not found"},
                status=404,
            )  # Not Found
        simulator = conversation_sessions[session_id]

    # Stop the conversation
    success = await simulator.stop()
    cleanup_session(session_id=session_id)

    if success:
        return web.json_response(
            {
                "success": True,
                "session_id": session_id,
                "message": f"Conversation with session ID {session_id} stopped successfully",
            },
            status=200,
        )
    else:
        return web.json_response(
            {
                "success": False,
                "error": f"Failed to stop conversation with session ID {session_id}",
            },
            status=500,
        )  # Internal Server Error


async def cleanup_session(session_id: str):
    """Remove a conversation session from the cache."""
    if not session_id:
        return  # Bad Request

    # Check if session exists with proper locking
    async with sessions_lock:
        if session_id not in conversation_sessions:
            return

        # Get reference to simulator before potentially removing it
        simulator = conversation_sessions[session_id]

    # Stop the conversation if running (outside the lock to avoid blocking)
    if simulator.is_running:
        await simulator.stop()

    # Remove from session cache with proper locking
    async with sessions_lock:
        # Check again in case it was removed while we were stopping
        if session_id in conversation_sessions:
            del conversation_sessions[session_id]


async def on_startup(app):
    """Initialize resources when the application starts."""
    logger.info("Initializing message queue handler...")
    logger.info("Conversation simulator service started")


async def on_shutdown(app):
    """Clean up resources when the application shuts down."""
    logger.info("Shutting down message queue handler...")

    # Stop and clean up all active conversations
    logger.info(
        f"Cleaning up {len(conversation_sessions)} active conversation sessions..."
    )
    for session_id, simulator in list(conversation_sessions.items()):
        if simulator.is_running:
            await simulator.stop()
        del conversation_sessions[session_id]

    logger.info("Conversation simulator service stopped")


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

    # Start server
    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    # Get the host and port from DefaultConfig
    host = DefaultConfig.SERVICE_HOST
    port = DefaultConfig.SERVICE_PORT
    
    # Use start_server directly (no need for asyncio.to_thread)
    start_server(host=host, port=port)
