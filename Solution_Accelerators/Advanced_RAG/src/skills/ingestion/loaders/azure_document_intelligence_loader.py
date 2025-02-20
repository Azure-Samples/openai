import os
from typing import Optional

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import (
    AnalyzeDocumentRequest,
    AnalyzeResult,
    ContentFormat,
    DocumentAnalysisFeature,
)
from azure.core.exceptions import HttpResponseError
from common.telemetry.app_logger import AppLogger

class AzureDocumentIntelligenceDocLoader():
    '''
    Azure Document Intelligence service based document loader to invoke analysis upon request.
    '''
    def __init__(
        self,
        azure_document_intelligence_endpoint: str,
        azure_document_intelligence_key: str,
        logger: AppLogger,
        document_intelligence_model: str = "prebuilt-layout"
    ) -> None:
        self.document_intelligence_model = document_intelligence_model

        self.document_analyzer_client = DocumentIntelligenceClient(
            endpoint=azure_document_intelligence_endpoint,
            credential=AzureKeyCredential(azure_document_intelligence_key)
        )
        self.logger = logger

    async def analyze_document(self, document_path: str, task_id: str) -> Optional[AnalyzeResult]:
        '''
        Analyzes the document as document_path using Azure Document Intelligence
        service.
        Return AnalyzeResult containing individual components of the document including
        tables, paragraphs and page-wise content.
        '''
        if not os.path.isfile(document_path):
            self.logger.error("Document path is invalid. Skipping document analysis.")
            return None

        with open(document_path, "rb") as fd:
            document = fd.read()

        try:
            analyze_document_request = AnalyzeDocumentRequest(bytes_source=document)
            poller = await self.document_analyzer_client.begin_analyze_document(
                self.document_intelligence_model,
                analyze_document_request,
                features=[DocumentAnalysisFeature.OCR_HIGH_RESOLUTION],
                output_content_format=ContentFormat.MARKDOWN
            )

            self.logger.info(f"Task {task_id}. Analyzing {document_path} with Azure Document Intelligence service..")
            return await poller.result()
        except HttpResponseError as http_ex:
            self.logger.error(f"Azure Document Intelligence request failed with server error: {http_ex}")
        except Exception as ex:
            self.logger.error(f"Failed to analyze document. Error {ex}")

        return None