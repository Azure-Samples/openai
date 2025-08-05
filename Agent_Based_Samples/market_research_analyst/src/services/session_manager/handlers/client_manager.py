# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from aiohttp import web

from azure.ai.projects import AIProjectClient

from common.telemetry.app_logger import AppLogger
from common.utilities.task_queue_manager import TaskQueueManager
from common.contracts.orchestrator.response import Response as OrchestratorResponse
from common.exceptions import (
    ClientConnectionClosedException,
    MessageProcessingTimeoutError,
)

from handlers.conversation_handler import ConversationHandler
from handlers.websocket_handler import WebsocketHandler


class ClientManager:
    """
    Manages lifetime of a client connection.
    """

    def __init__(
        self,
        session_id: str,
        logger: AppLogger,
        ai_foundry_project_client: AIProjectClient,
        task_manager: TaskQueueManager,
        max_response_timeout: int,
    ):
        self.logger = logger
        self.session_id = session_id

        self.ai_foundry_project_client = ai_foundry_project_client
        self.task_manager = task_manager
        self.max_response_timeout = max_response_timeout
        self._conversation_handler: ConversationHandler = None
        self._connection_handler: WebsocketHandler = None

    async def try_accept_connection_async(self, session_id, client_request: web.Request):
        """
        Accepts an incoming WebSocket connection and adds it to the cache.

        Raises:
            KeyError: If the connection ID already exists in the cache.
            MessageProcessingTimeoutError: If the message processing times out.
            ClientConnectionClosedException: If the client connection is closed unexpectedly.
            Exception: For any other errors during connection handling.
        """
        self.logger.info("Connection request received from client.")

        error = None
        try:
            # Create conversation handler to handle incoming chat requests
            self._conversation_handler = ConversationHandler(
                logger=self.logger,
                session_id=session_id,
                task_manager=self.task_manager,
                ai_foundry_project_client=self.ai_foundry_project_client,
                max_response_timeout=self.max_response_timeout,
            )

            # Create connection handler and try upgrading current request to websockets.
            self._connection_handler = WebsocketHandler(
                logger=self.logger,
                session_id=self.session_id,
                on_message_received_callback=self._conversation_handler.handle_request_message_async,
            )
            await self._connection_handler.upgrade_connection_async(session_id, client_request)

            # Start streaming messages from client.
            await self._connection_handler.start_client_request_stream_async(session_id)
        except KeyError as ke:
            error = str(ke)
            self.logger.error(f"Connection already exists. Error: {error}")
        except MessageProcessingTimeoutError as te:
            error = str(te)
            self.logger.error(f"Failed to accept client request. Error: {error}")
        except ClientConnectionClosedException as ce:
            error = str(ce)
            self.logger.info(f"Client connection closed. Error: {error}")
        except Exception as ex:
            error = str(ex)
            self.logger.error(f"Failed to accept client request. Error: {error}")
        finally:
            await self.close_connection_async(session_id=session_id, message=error)
            self._connection_handler.shutdown()

    async def close_connection_async(self, session_id: str, message: str = None, shutdown=False):
        """
        Closes a WebSocket connection for the given session ID.
        """
        try:
            await self._connection_handler.close_async(
                message="Client connection closed due to server error." if not message else message, shutdown=shutdown
            )
            self.logger.info(f"Session {session_id} closed successfully.")
        except Exception as ex:
            self.logger.error(f" to remove connection {session_id}. Error: {ex}")

    async def handle_chat_response_async(self, start_response: OrchestratorResponse):
        """
        Handles user message response from the conversation handler and sends it to the client.
        """
        chat_response = await self._conversation_handler.create_user_response_async(start_response)
        return await self._connection_handler.send_message_async(start_response.session_id, chat_response)
