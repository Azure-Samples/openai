# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from typing import Optional
from common.clients.content_understanding.content_understanding_client import AzureContentUnderstandingClient
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from semantic_kernel.functions.kernel_function_decorator import kernel_function

from common.telemetry.app_logger import AppLogger
from models.content_understanding_settings import (
    ContentUnderstandingSettings,
)


class ContentUnderstandingPlugin:
    """Plugin for handling content understanding tasks."""

    client: AzureContentUnderstandingClient = None
    utility_bill_analyzer_id: str = None
    drivers_license_analyzer_id: str = None
    income_statement_analyzer_id: str = None
    logger: AppLogger = None

    def __init__(
        self,
        logger: AppLogger,
        content_understanding_settings: ContentUnderstandingSettings,
    ):
        self.logger = logger
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
        self.client = AzureContentUnderstandingClient(
            endpoint=content_understanding_settings.endpoint,
            subscription_key=content_understanding_settings.subscription_key,
            api_version=content_understanding_settings.api_version,
            token_provider=token_provider,
            x_ms_useragent="azure-ai-content-understanding-python/content_extraction",  # This header is used for sample usage telemetry, please comment out this line if you want to opt out.
        )
        self.utility_bill_analyzer_id = content_understanding_settings.utility_bill_analyzer_id
        self.drivers_license_analyzer_id = content_understanding_settings.drivers_license_analyzer_id
        self.income_statement_analyzer_id = content_understanding_settings.income_statement_analyzer_id

    def _get_fields_from_result(self, result: dict) -> dict:
        """Extract fields from the analysis result."""
        if result["status"].lower() != "succeeded":
            self.logger.error(f"Utility bill analysis failed: {result["status"]}")
            return {"error": "Utility bill analysis failed."}
        if "result" in result and "contents" in result["result"] and len(result["result"]["contents"]) > 0:
            return {"extracted_fields": result["result"]["contents"][0]["fields"]}
        return {}

    @kernel_function(
        description="Analyze a utility bill for extracting customer information for loan application. This takes the uri of the file as input."
    )
    async def analyze_utility_bill(self, file_uri: str) -> dict:
        try:
            response = self.client.begin_analyze(
                analyzer_id=self.utility_bill_analyzer_id, file_location=file_uri, file_data=""
            )
            result = self.client.poll_result(response=response)
            extracted_fields = self._get_fields_from_result(result)
            self.logger.info(f"Utility bill analysis result: {extracted_fields}")
            return {"utility_bill_analysis": extracted_fields}
        except Exception as e:
            self.logger.error(f"Error analyzing utility bill: {str(e)}")
            return {"error": str(e)}

    @kernel_function(
        description="Analyze a driver's license for extracting customer information for loan application. This takes the uri of the file as input."
    )
    def analyze_drivers_license(self, file_uri: str) -> dict:
        try:
            response = self.client.begin_analyze(
                analyzer_id=self.drivers_license_analyzer_id, file_location=file_uri, file_data=""
            )
            result = self.client.poll_result(response=response)
            extracted_fields = self._get_fields_from_result(result)
            self.logger.info(f"Driver's license analysis result: {extracted_fields}")
            return {"drivers_license_analysis": extracted_fields}
        except Exception as e:
            self.logger.error(f"Error analyzing driver's license: {str(e)}")
            return {"error": str(e)}

    @kernel_function(
        description="Analyze a income statement for extracting customer information for loan application. This takes the uri of the file as input."
    )
    def analyze_income_statement(self, file_uri: str) -> dict:
        try:
            response = self.client.begin_analyze(
                analyzer_id=self.income_statement_analyzer_id, file_location=file_uri, file_data=""
            )
            result = self.client.poll_result(response=response)
            extracted_fields = self._get_fields_from_result(result)
            self.logger.info(f"Income statement analysis result: {extracted_fields}")
            return {"income_statement_analysis": extracted_fields}
        except Exception as e:
            self.logger.error(f"Error analyzing income statement: {str(e)}")
            return {"error": str(e)}
