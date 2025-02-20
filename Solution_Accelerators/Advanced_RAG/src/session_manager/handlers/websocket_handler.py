import asyncio
import json
from typing import Callable

from aiohttp import web
from aiohttp.http_websocket import WSCloseCode

from common.contracts.orchestrator.bot_response import BotResponse
from common.exceptions import ClientConnectionClosedException
from common.telemetry.app_logger import AppLogger


class WebsocketHandler:
    """
    Handles WebSocket connections by accepting incoming messages, sending messages to clients
    and closing connections when required.
    """
    def __init__(self, connection_id: str, logger: AppLogger, handle_request_message_async: Callable):
        self.connection_id = connection_id
        self.logger = logger
        self.websocket = None
        self._handle_request_message_async = handle_request_message_async
        self._message_queue = asyncio.Queue()
        self._process_message_task = asyncio.create_task(self.process_message_queue_async())

    def shutdown(self):
        """
        Cancels the message queue task.
        """
        self.logger.info(f"Shutting down Websocket handler for connection {self.connection_id}.")
        self._process_message_task.cancel()

    async def upgrade_connection_async(self, connection_id: str, request: web.Request) -> web.WebSocketResponse:
        # UPGRADE client request to WebSocket.
        websocket = web.WebSocketResponse()
        await websocket.prepare(request)

        self.websocket = websocket
        self.logger.info(f"Client request upgraded to Websockets successfully for connection {connection_id}.")

    async def send_message_async(self, connection_id: str, message, json: bool = False):
        """
        Send a message to the client over the websocket connection.
        Supports sending strings, bytes, or serializable Python objects (as JSON).
        """
        if self.websocket.closed or not self.websocket.prepared:
            self.logger.error(f"Websocket is not available for connection {connection_id}")
            raise Exception("Websocket is not available.")

        self.logger.info(f"Sending Websocket message for connection {connection_id}..")
        if isinstance(message, str):
            if json:
                await self.websocket.send_json(message)
            else:
                await self.websocket.send_str(message)
        elif isinstance(message, bytes):
            await self.websocket.send_bytes(message)

        self.logger.info(f"Websocket message sent to the client for connection {connection_id}.")

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
                self.logger.info(f"Processing message for connection {self.connection_id}")
                message = await self._message_queue.get()
                await self._handle_request_message_async(message)
                self.logger.info(f"Message processed successfully for connection {self.connection_id}")
            except Exception as ex:
                self.logger.error(f"Failed to process message. Error: {ex}")
                await self.drain_queue()  # Clear the queue
                if not message:
                    self.logger.error("Message is empty.")
                    continue
                message_object = json.loads(message)
                error_message = BotResponse(
                    connection_id=self.connection_id,
                    answer={},
                    error=str(ex),
                    conversation_id=message_object.get("conversation_id"),
                    dialog_id=message_object.get("dialog_id")
                )
                await self.send_message_async(self.connection_id, error_message.model_dump_json())

    async def start_client_request_stream_async(self, connection_id: str):
        """
        Handle incoming messages from the client. on_message_received will be invoked with the incoming
        message payload.
        """
        async for message in self.websocket:
            if message.type == web.WSMsgType.TEXT:
                self.logger.info(f"Websocket client: received message for connection {connection_id}")
                await self._message_queue.put(message.data)
                self.logger.info(f"Websocket client: message queued for processing. Connection {connection_id}")
            elif message.type == web.WSMsgType.CLOSE:
                self.logger.info(f"Client connection close requested by connection {connection_id}")
                await self.websocket.close()
                raise ClientConnectionClosedException("Client connection closed by client.")
            elif message.type == web.WSMsgType.ERROR:
                self.logger.error(f"Client connection {connection_id} closed with error: {self.websocket.exception()}")
                raise self.websocket.exception()
