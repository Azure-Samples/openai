import asyncio
import json
import time

from config import DefaultConfig
from safety.image_moderator import (
    ImageModerator,
    ImageSizeException,
    UnsafeImageException,
)
from utils.adaptive_cards import AdaptiveCardConverter
from utils.asyncio_event_util import AsyncIOEventWithTimeout

from common.clients.services.data_client import DataClient
from common.clients.services.orchestrator_client import OrchestratorClient
from common.contracts.common.conversation import *
from common.contracts.common.error import Error
from common.contracts.common.user_message import UserMessage
from common.contracts.common.user_prompt import PayloadType
from common.contracts.orchestrator.answer import Answer
from common.contracts.orchestrator.bot_request import BotRequest
from common.contracts.orchestrator.bot_response import BotResponse
from common.contracts.session_manager.chat_request import ChatRequest, ResponseMode
from common.contracts.session_manager.chat_response import ChatResponse
from common.contracts.session_manager.scenario import Scenario
from common.exceptions import MessageProcessingTimeoutError
from common.telemetry.app_logger import AppLogger
from common.utilities.blob_store import BlobStoreHelper
from common.utilities.task_manager import TaskManager


class ConversationHandler:
    def __init__(
        self,
        logger: AppLogger,
        data_client: DataClient,
        adaptive_card_converter: AdaptiveCardConverter,
        connection_id: str,
        task_manager: TaskManager,
        scenario: Scenario,
        max_response_timeout: int = 30,
    ) -> None:
        self.logger = logger
        self.data_client = data_client
        self.connection_id = connection_id
        self.task_manager = task_manager
        self.scenario = scenario
        self.max_response_timeout = max_response_timeout
        self.adaptive_card_converter = adaptive_card_converter

        self._current_message = None
        self._image_uris = None
        self._message_processing_status_event = AsyncIOEventWithTimeout()

    async def handle_chat_message(self, chat_request: ChatRequest):
        user_id = chat_request.user_id
        conversation_id = chat_request.conversation_id
        dialog_id = chat_request.dialog_id
        user_profile = chat_request.user_profile

        base_properties = {
            "ApplicationName": "SESSION_MANAGER_SERVICE",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "dialog_id": dialog_id,
        }
        self.logger.set_base_properties(base_properties)

        self.logger.info("Chat request received.")
        # initialize micro service clients
        data_service_uri = DefaultConfig.DATA_SERVICE_URI
        data_client = DataClient(data_service_uri, self.logger)

        # Pick right orchestrator URL based on scenario
        orchestrator_service_uri = (
            DefaultConfig.RETAIL_ORCHESTRATOR_SERVICE_URI
            if self.scenario == Scenario.RETAIL
            else DefaultConfig.RAG_ORCHESTRATOR_SERVICE_URI
        )
        orchestrator_client = OrchestratorClient(orchestrator_service_uri, self.logger)

        user_message = await self.__create_user_message(chat_request)

        # create or get chat session
        chat_session: Conversation
        chat_session = data_client.get_chat_session(user_id, conversation_id)
        self.logger.info(f"Got chat session for user {user_id} and session {conversation_id}")

        try:
            # generated messages
            start = time.monotonic()

            messages = chat_session.generate_text_history()
            messages.append(TextHistory(role="user", content=user_message.get_user_message_str()))

            if DefaultConfig.PRUNE_SEARCH_RESULTS_FROM_HISTORY_ON_PRODUCT_SELECTION.lower() == "true":
                if user_message.has_product_payload():
                    pruned_messages = []
                    for message in messages:
                        if message.role == "assistant":
                            pruned_messages.append(TextHistory(role="assistant", content="<SEARCH-RESULTS-PRUNED>"))
                        else:
                            pruned_messages.append(message)
                    messages = pruned_messages

            message_list = [message.model_dump() for message in messages]

            # start orchestration to generate a bot response
            bot_request = BotRequest(
                connection_id=self.connection_id,
                user_id=user_id,
                conversation_id=conversation_id,
                dialog_id=dialog_id,
                messages=message_list,
                locale=next(
                    payload.locale for payload in chat_request.message.payload if payload.type == PayloadType.TEXT
                ),
                user_profile=user_profile,
                overrides=chat_request.overrides,
            )
            bot_response, status_code = orchestrator_client.start(bot_request)

            # update chat session, if there was a successful response generated
            if status_code == 200 and not bot_response.error and bot_response.answer.answer_string:
                bot_message = BotMessage(payload=bot_response.answer.answer_string)
                dialog = Dialog(user_message=user_message, bot_message=bot_message)
                data_client.add_dialog_to_chat_session(user_id, conversation_id, dialog)

                self.logger.info(f"added user dialog to chat session for user {user_id} and session {conversation_id}")

            duration = (time.monotonic() - start) * 1000

            additional_properties = {
                "request": bot_request.model_dump_json(),
                "response": bot_response.model_dump_json(),
                "duration_ms": duration,
            }
            self.logger.info(f"Finished chat request", properties=additional_properties)
            return (
                ChatResponse(
                    connection_id=bot_response.connection_id,
                    dialog_id=bot_response.dialog_id,
                    conversation_id=bot_response.conversation_id,
                    user_id=bot_response.user_id,
                    answer=bot_response.answer,
                    error=bot_response.error,
                ),
                200,
            )
        except ConnectionError as e:
            self.logger.exception(f"Exception in /chat: {e}")
            error = Error(
                error_str="Apologies, but I am unable to provide a response for this query. Please try again. I appreciate your understanding.",
                retry=True,
            )
            return (
                ChatResponse(
                    connection_id="",
                    dialog_id=dialog_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    answer=Answer(),
                    error=error,
                ),
                500,
            )
        except Exception as e:
            self.logger.exception(f"Exception in /chat: {e}")
            error = Error(
                error_str="Apologies, but I am unable to provide a response for this query. Please try again. I appreciate your understanding.",
                retry=True,
                status_code=500,
            )
            if (
                hasattr(e, "response")
                and hasattr(e.response, "status_code")
                and e.response.status_code in (429, 403, 503)
            ):
                if bot_response is not None and bot_response.error is not None:
                    return (
                        ChatResponse(
                            connection_id="",
                            dialog_id=dialog_id,
                            conversation_id=conversation_id,
                            user_id=user_id,
                            answer=Answer(),
                            error=bot_response.error,
                        ),
                        500,
                    )
            return (
                ChatResponse(
                    connection_id="",
                    dialog_id=dialog_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    answer=Answer(),
                    error=error,
                ),
                500,
            )

    async def validate_image_and_upload(self, chat_request: ChatRequest) -> list:
        content_safety_endpoint = f"https://{DefaultConfig.AZURE_CONTENT_SAFETY_SERVICE}.cognitiveservices.azure.com/"
        image_moderator = ImageModerator(content_safety_endpoint, self.logger)

        blob_store_helper = BlobStoreHelper(
            logger=self.logger,
            storage_account_name=DefaultConfig.AZURE_STORAGE_ACCOUNT,
            container_name=DefaultConfig.AZURE_STORAGE_IMAGE_CONTAINER,
        )
        base_properties = {
            "ApplicationName": "SESSION_MANAGER_SERVICE",
            "user_id": chat_request.user_id,
            "conversation_id": chat_request.conversation_id,
            "dialog_id": chat_request.dialog_id,
        }
        self.logger.set_base_properties(base_properties)

        try:
            # check if user uploaded images are safe and upload them to blobstore
            image_safety_tasks = []
            image_upload_tasks = []
            for item in chat_request.message.payload:
                if item.type == PayloadType.IMAGE:
                    if (
                        chat_request.overrides is not None
                        and chat_request.overrides.session_manager_runtime is not None
                        and chat_request.overrides.session_manager_runtime.check_safe_image_content is not None
                        and chat_request.overrides.session_manager_runtime.check_safe_image_content
                    ):
                        image_task = asyncio.create_task(image_moderator.is_safe_async(item.value))
                        image_safety_tasks.append(image_task)

                    image_upload_task = asyncio.create_task(blob_store_helper.upload_image_async(item))
                    image_upload_tasks.append(image_upload_task)

            await asyncio.gather(*image_safety_tasks)
            return await asyncio.gather(*image_upload_tasks)
        except UnsafeImageException as e:
            self.logger.exception(f"Exception in /chat payload: {e}")
            return ChatResponse(connection_id="", answer=Answer(), error=str(e), show_retry=False), 400
        except ImageSizeException as e:
            self.logger.exception(f"Exception in /chat payload: {e}")
            return ChatResponse(connection_id="", answer=Answer(), error=str(e), show_retry=False), 400
        except Exception as e:
            self.logger.exception(f"Exception in /chat payload: {e}")
            return ChatResponse(connection_id="", answer=Answer(), error=str(e), show_retry=True), 500

    async def handle_request_message_async(self, message: str) -> None:
        """
        Handles incoming message payload to chat completion.

        Raises:
            MessageProcessingTimeoutError if a message could not be processed in allocated time.
        """
        if not message:
            self.logger.warning(f"Incorrect message payload received for connection {self.connection_id}")
            raise Exception("Incorrect message payload.")

        # Validate incoming message payload.
        self.logger.warning(f"Request message received. Validating payload received for connection {self.connection_id}")
        request_json = json.loads(message)
        chat_request = ChatRequest(**request_json)

        user_id = chat_request.user_id
        conversation_id = chat_request.conversation_id
        dialog_id = chat_request.dialog_id
        user_profile = chat_request.user_profile

        base_properties = {
            "ApplicationName": "SESSION_MANAGER_SERVICE",
            "user_id": user_id,
            "conversation_id": conversation_id,
            "dialog_id": dialog_id,
        }
        self.logger.set_base_properties(base_properties)
        self.logger.info(f"Handling message for connection. {self.connection_id}")
        self._current_message = chat_request

        user_message = await self.__create_user_message(chat_request)

        # Create or Get chat session
        try:
            chat_session: Conversation = self.data_client.get_chat_session(user_id, conversation_id)
            self.logger.info(f"Got chat session for user {user_id} and session {conversation_id}")
        except Exception as ex:
            self.logger.exception(
                f"Exception while fetching chat session for user_id {user_id} and conversation_id {conversation_id}: {ex}"
            )
            raise

        try:
            # Generate history for current client.
            messages = chat_session.generate_text_history()
            messages.append(TextHistory(role="user", content=user_message.get_user_message_str()))

            if DefaultConfig.PRUNE_SEARCH_RESULTS_FROM_HISTORY_ON_PRODUCT_SELECTION.lower() == "true":
                if user_message.has_product_payload():
                    pruned_messages = []
                    for message in messages:
                        if message.role == "assistant":
                            pruned_messages.append(TextHistory(role="assistant", content="<SEARCH-RESULTS-PRUNED>"))
                        else:
                            pruned_messages.append(message)
                    messages = pruned_messages

            message_list = [message.model_dump() for message in messages]
            self.logger.info(f"Generated message history for user {user_id} and session {conversation_id}")
            # start orchestration to generate a bot response
            bot_request = BotRequest(
                connection_id=self.connection_id,
                user_id=user_id,
                conversation_id=conversation_id,
                dialog_id=dialog_id,
                messages=message_list,
                locale=next(
                    (payload.locale for payload in chat_request.message.payload if payload.type == PayloadType.TEXT),
                    None,
                ),
                user_profile=user_profile,
                overrides=chat_request.overrides,
            )

            # Queue chat request in task queue
            await self.task_manager.submit_task(bot_request.model_dump_json())

            # Create event for message response and await response until timeout.
            is_message_response_received = await self._message_processing_status_event.wait(
                timeout=self.max_response_timeout
            )
            if not is_message_response_received:
                self.logger.warning(
                    f"Timeout occurred waiting for message response for connection {self.connection_id}"
                )
                raise MessageProcessingTimeoutError("Request timed out.")
            self.logger.info(f"Message response received for connection {self.connection_id}")
        except Exception as ex:
            self.logger.exception(f"Exception while queueing chat request task: {ex}")
            raise
        finally:
            # Reset current message processing status upon response
            self._message_processing_status_event.clear()
            self.logger.info(f"Reset message processing status for connection {self.connection_id}")

    async def create_chat_response_async(self, bot_response: BotResponse, scenario=Scenario.RAG) -> str:
        user_message = await self.__create_user_message(self._current_message)

        additional_properties = {
            "request": self._current_message.model_dump_json(),
            "response": bot_response.model_dump_json(),
            "duration_ms": "",  # TODO: handle request-response duration under new architecture
        }
        self.logger.info(f"Received chat response.", properties=additional_properties)

        # Update chat session: if there was a successful response generated
        # AND if the current response is the final answer.
        # Appending intermediate responses to chat history can be counter-productive.
        if not bot_response.error and bot_response.answer.answer_string and bot_response.answer.data_points:
            botResponse = BotMessage(payload=bot_response.answer.answer_string)
            dialog = Dialog(user_message=user_message, bot_message=botResponse)
            self.data_client.add_dialog_to_chat_session(
                self._current_message.user_id, self._current_message.conversation_id, dialog
            )
            self.logger.info(
                f"Added user dialog to chat session for user {self._current_message.user_id} and session {self._current_message.conversation_id}"
            )

            # Unblock client message processing once history is updated.
            self._message_processing_status_event.set()
            self.logger.info(
                f"Final answer received. Unblocking message stream from client for connection {bot_response.connection_id}."
            )

        # Convert start_response to chat_response
        chat_response = ChatResponse(
            connection_id=bot_response.connection_id,
            dialog_id=bot_response.dialog_id,
            conversation_id=bot_response.conversation_id,
            user_id=bot_response.user_id,
            answer=bot_response.answer,
            error=bot_response.error,
        )

        if (
            hasattr(self._current_message, "response_mode")
            and self._current_message.response_mode == ResponseMode.AdaptiveCard
        ):
            return json.dumps(self.adaptive_card_converter.to_adaptive_with_citations(chat_response.model_dump_json()))

        return chat_response.model_dump_json()

    async def __create_user_message(self, chat_request: ChatRequest) -> UserMessage:
        if self.scenario == Scenario.RETAIL:
            image_uris = await self.validate_image_and_upload(chat_request)

        user_message = UserMessage()

        i = 0
        for item in chat_request.message.payload:
            payload_type = PayloadType(item.type)

            match (payload_type):
                case PayloadType.TEXT:
                    user_message.add_text_payload(item.value)
                case PayloadType.IMAGE:
                    img_uri = image_uris[i]  # blob_store_helper.upload_image_to_blob_store(item)
                    user_message.add_img_uri_payload(str(img_uri))
                    i += 1
                case PayloadType.PRODUCT:
                    user_message.add_product_payload(item.value)
        return user_message