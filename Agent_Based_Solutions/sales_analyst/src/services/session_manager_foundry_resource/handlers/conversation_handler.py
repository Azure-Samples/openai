# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import asyncio
import json

from azure.ai.projects import AIProjectClient
from config import DefaultConfig
from utils.asyncio_event_util import AsyncIOEventWithTimeout
from common.telemetry.trace_context import inject_trace_context

from common.contracts.common.answer import Answer
from common.contracts.common.user_message import UserMessage
from common.contracts.common.user_query import PayloadType
from common.contracts.orchestrator.request import Request as OrchestratorRequest
from common.contracts.orchestrator.response import Response as OrchestratorResponse
from common.contracts.session_manager.request import Request
from common.contracts.session_manager.response import Response
from common.exceptions import MessageProcessingTimeoutError
from common.safety.image_safety import (
    ImageModerator,
    ImageSizeException,
    UnsafeImageException,
)
from common.telemetry.app_logger import AppLogger
from common.utilities.blob_store_helper import BlobStoreHelper
from common.utilities.task_queue_manager import TaskQueueManager


class ConversationHandler:
    """
    Handles the conversation for a specific connection, including message processing via orchestrator and response generation.
    """

    def __init__(
        self,
        logger: AppLogger,
        session_id: str,
        task_manager: TaskQueueManager,
        ai_foundry_project_client: AIProjectClient,
        max_response_timeout: int = 30,
    ) -> None:
        self.logger = logger
        self.session_id = session_id
        self.task_manager = task_manager
        self.ai_foundry_project_client = ai_foundry_project_client
        self.max_response_timeout = max_response_timeout

        self._current_message = None
        self._image_uris = None
        self._message_processing_status_event = AsyncIOEventWithTimeout()

        # Azure AI Foundry threads are created to track each conversation.
        # A single thread can have multiple messages representing a  multi-turn conversation.
        self.thread_id = None

    async def validate_image_and_upload(self, request: Request) -> list:
        """
        Validates and uploads images from the request payload to Azure Blob Storage.

        Raises:
            UnsafeImageException: If any image is found unsafe.
            ImageSizeException: If any image exceeds the maximum allowed size.
            Exception: For any other unexpected errors during image validation or upload.

        Returns:
            list: A list of URIs for the successfully uploaded images.
        """
        content_safety_endpoint = f"https://{DefaultConfig.AZURE_CONTENT_SAFETY_SERVICE}.cognitiveservices.azure.com/"
        image_moderator = ImageModerator(content_safety_endpoint, self.logger)

        blob_store_helper = BlobStoreHelper(
            logger=self.logger,
            storage_account_name=DefaultConfig.AZURE_STORAGE_ACCOUNT,
            container_name=DefaultConfig.AZURE_STORAGE_IMAGE_CONTAINER,
        )
        base_properties = {
            "ApplicationName": "SESSION_MANAGER_SERVICE",
            "user_id": request.user_id,
        }
        self.logger.set_base_properties(base_properties)

        try:
            # check if user uploaded images are safe and upload them to blobstore
            image_safety_tasks = []
            image_upload_tasks = []
            for item in request.message.payload:
                if item.type == PayloadType.IMAGE:
                    # Check safety
                    image_task = asyncio.create_task(image_moderator.is_safe_async(item.value))
                    image_safety_tasks.append(image_task)

                    # Upload
                    image_upload_task = asyncio.create_task(blob_store_helper.upload_image_async(item.value))
                    image_upload_tasks.append(image_upload_task)

            await asyncio.gather(*image_safety_tasks)
            return await asyncio.gather(*image_upload_tasks)
        except UnsafeImageException as e:
            self.logger.exception(f"Exception in /query payload: {e}")
            return Response(session_id="", answer=Answer(), error=str(e), show_retry=False), 400
        except ImageSizeException as e:
            self.logger.exception(f"Exception in /query payload: {e}")
            return Response(session_id="", answer=Answer(), error=str(e), show_retry=False), 400
        except Exception as e:
            self.logger.exception(f"Exception in /query payload: {e}")
            return Response(session_id="", answer=Answer(), error=str(e), show_retry=True), 500

    async def handle_request_message_async(self, message: str) -> None:
        """
        Handles incoming message payload asynchronously, validates it, and processes it to generate a bot response.
        This method will block until a response is received or the timeout occurs.

        Raises:
            MessageProcessingTimeoutError if a message could not be processed in allocated time.
        """
        if not message:
            self.logger.warning(f"Incorrect message payload received for session {self.session_id}")
            raise Exception("Incorrect message payload.")

        # Validate incoming message payload.
        self.logger.warning(f"Request message received. Validating payload received for session {self.session_id}")
        request_json = json.loads(message)
        user_request = Request(**request_json)

        user_id = user_request.user_id
        user_profile = user_request.user_profile
        dialog_id = user_request.dialog_id

        base_properties = {
            "ApplicationName": "SESSION_MANAGER_SERVICE",
            "session_id": self.session_id,
            "user_id": user_id,
            "dialog_id": dialog_id,
        }
        self.logger.set_base_properties(base_properties)
        self.logger.info(f"Handling message for session {self.session_id}")
        self._current_message = user_request

        user_message = await self.__create_user_message(user_request)

        try:
            if self.thread_id is None:
                self.thread_id = self.ai_foundry_project_client.agents.threads.create()
                self.logger.info(f"Thread {self.thread_id} successfully created for session {self.session_id}")

            # start orchestration to generate a bot response
            orchestrator_request = OrchestratorRequest(
                trace_id={},
                session_id=self.session_id,
                dialog_id=dialog_id,
                user_id=user_id,
                thread_id=self.thread_id.id,
                message=user_message.get_user_message_str(),
                locale=next(
                    (payload.locale for payload in user_request.message.payload if payload.type == PayloadType.TEXT),
                    None,
                ),
                user_profile=user_profile,
                additional_metadata=user_request.additional_metadata,
                authorization=user_request.authorization,
            )
            inject_trace_context(orchestrator_request.trace_id)

            # Queue chat request in task queue
            await self.task_manager.submit_task(orchestrator_request.model_dump_json())

            # Create event for message response and await response until timeout.
            is_message_response_received = await self._message_processing_status_event.wait(
                timeout=self.max_response_timeout
            )
            if not is_message_response_received:
                self.logger.warning(f"Timeout occurred waiting for message response for session {self.session_id}")
                raise MessageProcessingTimeoutError("Request timed out.")
            self.logger.info(f"Message response received for session {self.session_id}")
        except Exception as ex:
            self.logger.exception(f"Exception while queueing chat request task: {ex}")
            raise
        finally:
            # Reset current message processing status upon response
            self._message_processing_status_event.clear()
            self.logger.info(f"Reset message processing status for session {self.session_id}")

    async def create_user_response_async(self, orchestrator_response: OrchestratorResponse) -> str:
        """
        Handles the response from the orchestrator and converts it into a user response.

        Returns:
            str: JSON string of the user response.
        """
        additional_properties = {
            "request": self._current_message.model_dump_json(),
            "response": orchestrator_response.model_dump_json(),
            "duration_ms": "",  # TODO: handle request-response duration under new architecture
        }
        self.logger.info(f"Received response.", properties=additional_properties)

        # If the response is final, unblock the client message processing.
        # This will unblock further message processing from the client.
        if not orchestrator_response.error and orchestrator_response.answer.is_final:
            self._message_processing_status_event.set()
            self.logger.info(
                f"Final answer received. Unblocking message stream from client for session {orchestrator_response.session_id}."
            )

        # Convert start_response to chat_response
        response = Response(
            session_id=orchestrator_response.session_id,
            dialog_id=orchestrator_response.dialog_id,
            thread_id=orchestrator_response.thread_id,
            user_id=orchestrator_response.user_id,
            answer=orchestrator_response.answer,
            error=orchestrator_response.error,
        )

        return response.model_dump_json()

    async def __create_user_message(self, request: Request) -> UserMessage:
        """
        Creates a UserMessage object from the incoming request, validating and uploading images if necessary.

        Returns:
            UserMessage: The constructed UserMessage object containing text and image payloads.
        """
        if any(user_payload.type == PayloadType.IMAGE for user_payload in request.message.payload):
            image_uris = await self.validate_image_and_upload(request)

        user_message = UserMessage()

        i = 0
        for item in request.message.payload:
            payload_type = PayloadType(item.type)

            match (payload_type):
                case PayloadType.TEXT:
                    user_message.add_text_payload(item.value)
                case PayloadType.IMAGE:
                    img_uri = image_uris[i]
                    user_message.add_img_uri_payload(str(img_uri))
                    i += 1
        return user_message
