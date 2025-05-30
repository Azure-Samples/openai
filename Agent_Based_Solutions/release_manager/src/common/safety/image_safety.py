# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import base64
from azure.core.exceptions import HttpResponseError
from common.telemetry.app_logger import AppLogger
from azure.identity import DefaultAzureCredential

from azure.ai.contentsafety.aio import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeImageOptions, ImageData


class UnsafeImageException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ImageSizeException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ImageModerator:
    """
    Class for moderating images.
    """

    def __init__(self, cs_api_endpoint, logger: AppLogger) -> None:
        self.client = ContentSafetyClient(cs_api_endpoint, DefaultAzureCredential())
        self.logger = logger

    async def is_safe_async(self, content_str: str) -> bool:
        """
        Analyze the image for safety.
        """
        # Handle data URI scheme format (e.g., "data:image/png;base64,...")
        if content_str.startswith("data:"):
            # Extract the actual Base64 content after the comma
            try:
                content_str = content_str.split(",", 1)[1]
            except IndexError:
                self.logger.error("Invalid data URI format")
                raise ValueError("Invalid image format: Malformed data URI")

        try:
            content = base64.b64decode(content_str)
            request = AnalyzeImageOptions(image=ImageData(content=content))

            try:
                response = await self.client.analyze_image(request)
                for unsafe_category in response.get("categoriesAnalysis", []):
                    if unsafe_category.get("severity", 0) > 0:
                        self.logger.info(f"Unsafe image detected. Category: {unsafe_category.category}")
                        raise UnsafeImageException("Unsafe image detected")
            except HttpResponseError as e:
                # Currently content safety client wraps all errors in HttpResponseError.
                # ToDo: Move away from custom error handling once the client is updated.
                error_code = e.error.code
                error_message = e.error.message
                user_friendly_message = error_message.split("|")[0]
                if (
                    "InvalidRequestBody" in error_code.strip()
                    and "greater than the maximum allowed" in error_message.strip()
                ):
                    self.logger.error(f"Image size exceeds maximum allowed limits. Error: {error_message}")
                    raise ImageSizeException(f"Image size exceeds maximum allowed limits. {user_friendly_message}")

                self.logger.error(f"Analyzing the image for safety failed: {e}")
                raise e
        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            if "Incorrect padding" in str(e):
                self.logger.error("Base64 decoding error: Incorrect padding")
                raise ValueError("Invalid image format: Base64 encoding issue") from e
            raise e

        self.logger.info("Image passed safety check.")
        return True
