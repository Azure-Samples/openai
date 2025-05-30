# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from typing import Callable

import asyncio
from aiohttp import web
from aiohttp.http_websocket import WSCloseCode

from common.telemetry.app_logger import AppLogger
from common.exceptions import ClientConnectionClosedException
from common.contracts.orchestrator.response import Response as OrchestratorResponse


class WebsocketHandler:
    """
    Handles WebSocket connections by accepting incoming messages, sending messages to clients
    and closing connections when required.
    """

    def __init__(self, session_id: str, logger: AppLogger, on_message_received_callback: Callable):
        self.session_id = session_id
        self.logger = logger
        self.websocket = None
        self.on_message_received = on_message_received_callback
        self._message_queue = asyncio.Queue()
        self._process_message_task = asyncio.create_task(self.process_message_queue_async())

    def shutdown(self):
        """
        Cancels the message queue task.
        """
        self.logger.info(f"Shutting down Websocket handler for connection {self.session_id}.")
        self._process_message_task.cancel()

    async def upgrade_connection_async(self, session_id: str, request: web.Request) -> web.WebSocketResponse:
        # UPGRADE client request to WebSocket.
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)

        self.websocket = websocket
        self.logger.info(f"Client request upgraded to Websockets successfully for connection {session_id}.")

    async def send_message_async(self, session_id: str, message, json: bool = False):
        """
        Send a message to the client over the websocket connection.
        Supports sending strings, bytes, or serializable Python objects (as JSON).
        """
        if self.websocket.closed or not self.websocket.prepared:
            self.logger.error(f"Websocket is not available for connection {session_id}")
            raise Exception("Websocket is not available.")

        self.logger.info(f"Sending Websocket message for connection {session_id}..")
        if isinstance(message, str):
            if json:
                await self.websocket.send_json(message)
            else:
                await self.websocket.send_str(message)
        elif isinstance(message, bytes):
            await self.websocket.send_bytes(message)

        self.logger.info(f"Websocket message sent to the client for connection {session_id}.")

    async def close_async(self, code: WSCloseCode = WSCloseCode.OK, message: str = "", shutdown: bool = False):
        """
        Close the websocket connection.
        """
        if shutdown:
            code = WSCloseCode.GOING_AWAY

        return await self.websocket.close(code=code, message=message)

    async def drain_queue(self):
        """
        Drains the message queue.
        """
        while not self._message_queue.empty():
            try:
                self._message_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    async def process_message_queue_async(self):
        """
        Processes the message queue.
        """
        while True:
            try:
                self.logger.info(f"Processing message for connection {self.session_id}")
                message = await self._message_queue.get()
                await self.on_message_received(message)
                self.logger.info(f"Message processed successfully for connection {self.session_id}")
            except Exception as ex:
                self.logger.error(f"Failed to process message. Error: {ex}")
                await self.drain_queue()  # Clear the queue
                if not message:
                    self.logger.error("Message is empty.")
                    continue
                message_object = json.loads(message)
                error_message = OrchestratorResponse(
                    session_id=self.session_id,
                    answer={},
                    error=str(ex),
                    thread_id=message_object.get("thread_id"),
                )
                await self.send_message_async(self.session_id, error_message.model_dump_json())

    async def start_client_request_stream_async(self, session_id: str):
        """
        Handle incoming messages from the client. on_message_received will be invoked with the incoming
        message payload.
        """
        async for message in self.websocket:
            if message.type == web.WSMsgType.TEXT:
                self.logger.info(f"Websocket client: received message for connection {session_id}")
                await self._message_queue.put(message.data)
                self.logger.info(f"Websocket client: message queued for processing. Connection {session_id}")
            elif message.type == web.WSMsgType.CLOSE:
                self.logger.info(f"Client connection close requested by connection {session_id}")
                await self.websocket.close()
                raise ClientConnectionClosedException("Client connection closed by client.")
            elif message.type == web.WSMsgType.ERROR:
                self.logger.error(f"Client connection {session_id} closed with error: {self.websocket.exception()}")
                raise self.websocket.exception()
