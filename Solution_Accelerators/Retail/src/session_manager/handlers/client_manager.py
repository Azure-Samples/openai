from aiohttp import web
from handlers.conversation_handler import ConversationHandler
from handlers.websocket_handler import WebsocketHandler
from utils.adaptive_cards import AdaptiveCardConverter

from common.clients.services.data_client import DataClient
from common.contracts.orchestrator.bot_request import BotRequest
from common.contracts.orchestrator.bot_response import BotResponse
from common.contracts.session_manager.scenario import Scenario
from common.exceptions import (
    ClientConnectionClosedException,
    MessageProcessingTimeoutError,
)
from common.telemetry.app_logger import AppLogger
from common.utilities.task_manager import TaskManager


class ClientManager:
    """
    Manages lifetime of a client connection.
    """

    def __init__(
        self,
        connection_id: str,
        logger: AppLogger,
        data_client: DataClient,
        task_manager: TaskManager,
        adaptive_card_converter: AdaptiveCardConverter,
        max_response_timeout: int,
        scenario: Scenario,
    ):
        self.logger = logger
        self.connection_id = connection_id
        self.data_client = data_client
        self.task_manager = task_manager
        self.max_response_timeout = max_response_timeout
        self.adaptive_card_converter = adaptive_card_converter
        self.scenario = scenario
        self._conversation_handler: ConversationHandler = None
        self._connection_handler: WebsocketHandler = None

    async def try_accept_connection_async(self, connection_id, client_request: web.Request):
        """
        Accepts an incoming WebSocket connection and adds it to the cache.
        """
        self.logger.info("Connection request received from client.")

        error = None
        try:
            # Create conversation handler to handle incoming chat requests
            self._conversation_handler = ConversationHandler(
                logger=self.logger,
                connection_id=connection_id,
                data_client=self.data_client,
                adaptive_card_converter=self.adaptive_card_converter,
                task_manager=self.task_manager,
                max_response_timeout=self.max_response_timeout,
                scenario=self.scenario,
            )

            # Create connection handler and try upgrading current request to websockets.
            self._connection_handler = WebsocketHandler(
                self.connection_id, self.logger, self._conversation_handler.handle_request_message_async
            )
            await self._connection_handler.upgrade_connection_async(connection_id, client_request)

            # Start streaming messages from client.
            await self._connection_handler.start_client_request_stream_async(connection_id)
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
            await self.close_connection_async(connection_id=connection_id, message=error)
            self._connection_handler.shutdown()

    async def close_connection_async(self, connection_id: str, message: str = None, shutdown=False):
        """
        Closes a WebSocket connection.
        """
        try:
            await self._connection_handler.close_async(
                message="Client connection closed due to server error." if not message else message, shutdown=shutdown
            )
            self.logger.info(f"Connection {connection_id} closed successfully.")
        except Exception as ex:
            self.logger.error(f" to remove connection {connection_id}. Error: {ex}")

    async def handle_chat_response_async(self, start_response: BotResponse):
        """
        Handles chat message response.
        """
        chat_response = await self._conversation_handler.create_chat_response_async(start_response)
        return await self._connection_handler.send_message_async(start_response.connection_id, chat_response)

    async def handle_chat_response_scenario_specific_async(self, start_response: BotResponse, scenario: Scenario):
        """
        Handles chat message response for a specific scenario.
        """
        chat_response = await self._conversation_handler.create_chat_response_async(start_response, scenario)
        return await self._connection_handler.send_message_async(start_response.connection_id, chat_response)
