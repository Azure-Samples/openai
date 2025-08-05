# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from azure.ai.contentsafety.aio import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential

from common.telemetry.app_logger import AppLogger


class UnsafeTextException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class TextModerator:
    """
    Class for moderating text content.
    """

    def __init__(self, cs_api_endpoint, logger: AppLogger) -> None:
        self.client = ContentSafetyClient(cs_api_endpoint, DefaultAzureCredential())
        self.logger = logger

    async def is_safe_async(self, text: str) -> bool:
        """
        Analyze the text for safety.
        """
        self.logger.info("Analyzing user input text for safety.")

        try:
            request = AnalyzeTextOptions(text=text)
            response = await self.client.analyze_text(request)
            for unsafe_category in response.get("categoriesAnalysis", []):
                if unsafe_category.get("severity", 0) > 0:
                    self.logger.warning(f"Unsafe text detected. Category: {unsafe_category.category}")
                    return False
        except HttpResponseError as e:
            self.logger.error(f"Analyzing the text for safety failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error processing text: {e}")
            return False

        self.logger.info("User input passed safety check.")
        return True
