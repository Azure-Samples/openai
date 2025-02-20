import os
from typing import Optional

from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
from common.telemetry.app_logger import AppLogger

class LangChainDocLoader():
    '''
    Langchain Document Analyzer Client to invoke document analysis upon request.
    '''
    def __init__(
        self,
        document_intelligence_endpoint: str,
        document_intelligence_key: str,
        logger: AppLogger,
        document_intelligence_model: str = "prebuilt-layout"
    ) -> None:
        self.api_endpoint = document_intelligence_endpoint
        self.api_key = document_intelligence_key
        self.model = document_intelligence_model
        self.logger = logger

    def analyze_document(self, document_path: str, task_id: str) -> Optional[str]:
        '''
        Analyzes the document at document_path using Langchain document loader.
        Return a string representation of the document in MARKDOWN format.
        '''
        if not os.path.isfile(document_path):
            self.logger.error("Document path is invalid. Skipping document analysis.")
            return None

        loader = AzureAIDocumentIntelligenceLoader(
            file_path=document_path,
            api_key = self.api_key,
            api_endpoint = self.api_endpoint,
            api_model=self.model
        )

        try:
            self.logger.info(f"\nTask {task_id}. Analyzing {document_path} with Azure Document Intelligence service..")

            # Langchain loader returns a list, but all content is parsed as page_content
            # on the first element.
            return loader.load()[0].page_content
        except Exception as ex:
            self.logger.error(f"Task {task_id}. Failed to analyze document. Error {ex}")
            return None