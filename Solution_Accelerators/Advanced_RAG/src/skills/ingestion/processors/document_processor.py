import asyncio
import json
import os

from azure.ai.documentintelligence.models import AnalyzeResult
from clients.azure_storage_client import AzureStorageClient
from indexers.indexer import Indexer
from loaders.azure_document_intelligence_loader import (
    AzureDocumentIntelligenceDocLoader,
)
from loaders.langchain_document_loader import LangChainDocLoader
from models.models import DocumentIndexerRequestPayload
from splitters.markdown_text_splitter import MarkdownHeaderTextSplitter
from splitters.plaintext_splitter import PlainTextSplitter

from common.clients.openai.openai_client import AzureOpenAIClient
from common.telemetry.app_logger import AppLogger
from managers.task_status_manager import TaskStatusManager, TaskStatus


class DocumentProcessor:
    def __init__(self,
                 logger: AppLogger,
                 storage_client: AzureStorageClient,
                 search_endpoint: str,
                 document_loader: str,
                 document_splitter: str,
                 upload_dir: str,
                 document_intelligence_endpoint: str,
                 document_intelligence_key: str,
                 document_intelligence_model: str,
                 document_max_chunk_size: str,
                 markdown_header_split_config: str,
                 markdown_content_include_image_captions: bool,
                 azure_openai_endpoint: str,
                 azure_openai_embeddings_engine_name: str,
                 document_indexer_status_manager: TaskStatusManager
    ) -> None:
        self.logger = logger
        self.search_endpoint = search_endpoint
        self.storage_client = storage_client
        self.upload_dir = upload_dir
        self.document_indexer_status_manager = document_indexer_status_manager

        self._chunking_lock = asyncio.Lock()

        if document_loader == "azuredocumentintelligence":
            self.document_loader = AzureDocumentIntelligenceDocLoader(
                azure_document_intelligence_endpoint=document_intelligence_endpoint,
                azure_document_intelligence_key=document_intelligence_key,
                logger=logger,
                document_intelligence_model=document_intelligence_model
            )
        elif document_loader == "langchain":
            self.document_loader = LangChainDocLoader(
                document_intelligence_endpoint=document_intelligence_endpoint,
                azure_document_intelligence_key=document_intelligence_key,
                logger=logger,
                document_intelligence_model=document_intelligence_model
            )
        else:
            self.logger.error(f"Document loader {document_loader} is not supported.")
            raise Exception(f"Document loader {document_loader} is not supported.")

        if document_splitter == "plaintext":
            self.document_splitter = PlainTextSplitter(
                logger=logger,
                openai_client=AzureOpenAIClient(logger=logger, endpoint=azure_openai_endpoint, retry=True),
                embeddings_deployment_name=azure_openai_embeddings_engine_name,
                max_chunk_size=document_max_chunk_size,
                markdown_content_include_image_captions=markdown_content_include_image_captions
            )
        elif document_splitter == "markdown":
            self.document_splitter = MarkdownHeaderTextSplitter(
                logger=logger,
                openai_client=AzureOpenAIClient(logger=logger, endpoint=azure_openai_endpoint, retry=True),
                embeddings_deployment_name=azure_openai_embeddings_engine_name,
                max_chunk_size=document_max_chunk_size,
                markdown_content_include_image_captions=markdown_content_include_image_captions,
                azure_document_intelligence_endpoint=document_intelligence_endpoint,
                azure_document_intelligence_key=document_intelligence_key,
                headers_to_split_on=markdown_header_split_config
            )
        else:
            self.logger.error(f"Document splitter {document_splitter} is not supported.")
            raise Exception(f"Document splitter {document_splitter} is not supported.")

    async def process_async(self, message: bytes):
        payload = DocumentIndexerRequestPayload(**json.loads(message))
        self.logger.info(f"Task {payload.task_id}: Document Indexer: File received {payload.document_name}")
        await self.document_indexer_status_manager.set_task_status(payload.task_id, "Task is processing by document processor.", TaskStatus.PROCESSING)

        try:
            # Step 1: Analyze document using document loader service
            analysis: AnalyzeResult = await self.document_loader.analyze_document(document_path=payload.document_path, task_id=payload.task_id)
            if analysis is None:
                self.logger.error(f"Task {payload.task_id}: Document analysis failed for {payload.document_name}. Exiting.")

            # Step 2: Upload parsed document to Azure Storage for future analysis.
            upload_status = await self.storage_client.upload_parsed_document_async(blob_container_name=payload.storage_container_name,
                                                                                   content=analysis.content,
                                                                                   document_name=payload.document_name,
                                                                                   markdown=True,
                                                                                   task_id=payload.task_id)
            # DO NOT BLOCK indexing for failure to upload.
            if not upload_status:
                self.logger.warning(f"Task {payload.task_id}: Parsed Document upload failed for {payload.document_name}. Indexing will continue.")

            # Step 3: Once document is analyzed, generate individual chunks.
            async with self._chunking_lock:
                chunks = await self.document_splitter.generate_splits_async(document_file_path=payload.document_path,
                                                                            analyzed_document=analysis,
                                                                            reported_year=payload.reported_year,
                                                                            subsidiary=payload.subsidiary,
                                                                            task_id=payload.task_id)
                if len(chunks) == 0:
                    self.logger.error(f"Task {payload.task_id}: Document chunking failed for {payload.document_name}. Exiting.")

            # Step 4: Upload chunks in search index.
            indexer = Indexer(search_endpoint=self.search_endpoint, index_name=payload.index_name, logger=self.logger)
            result = await indexer.index_async(chunks, payload.task_id)
            if not result:
                self.logger.error(f"Task {payload.task_id}: Document indexing failed for {payload.document_name}. Exiting.")

            # Step 5: Upload document as individual pages in storage for Citations.
            upload_status = await self.storage_client.upload_file_by_page_async(blob_container_name=payload.storage_container_name,
                                                                                file_path=payload.document_path,
                                                                                task_id=payload.task_id)
            if not upload_status:
                self.logger.error(f"Task {payload.task_id}: Document upload by page failed for {payload.document_name}. Exiting.")
            await self.document_indexer_status_manager.set_task_status(payload.task_id, "Task processed by document processor.", TaskStatus.PROCESSED)
        except Exception as ex:
            self.logger.exception(f"Task {payload.task_id}: Document Indexer failed. {ex}")
            await self.document_indexer_status_manager.set_task_status(payload.task_id, f"An error occured while processing task: {ex}", TaskStatus.FAILED)
        finally:
            # Step 6: Clean up uploaded file for data privacy reasons.
            os.remove(payload.document_path)
            self.logger.info(f"Task {payload.task_id}: Document Indexer: uploaded file(s) cleaned up successfully")