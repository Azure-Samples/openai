from typing import List

from azure.search.documents.aio import SearchClient
from azure.identity import DefaultAzureCredential
from common.telemetry.app_logger import AppLogger

class Indexer:
    '''
    Indexes a document in Azure AI Search Index.
    '''
    def __init__(
        self,
        search_endpoint: str,
        index_name: str,
        logger: AppLogger
    ) -> None:
        self.search_client = SearchClient(
            endpoint=search_endpoint,
            credential=DefaultAzureCredential(),
            index_name=index_name
        )
        self.logger = logger

    async def index_async(self, chunks: List, task_id: str):
        '''
        Uploads individual chunks in an existing index.
        Note:
            Index MUST exist for this operation to succeed.
        '''
        if len(chunks) == 0:
            self.logger.error("No chunks found to upload. Skipping indexing operation.")
            return False

        try:
            results = await self.search_client.upload_documents(documents=chunks)
            succeeded = sum([1 for r in results if r.succeeded])
            self.logger.info(f"Task {task_id}. Index operation succeeded. Attempted: {len(results)} chunks. Succeeded: {succeeded} chunks.")
            return True
        except Exception as ex:
            self.logger.error(f"Task {task_id}. Failed to index chunk. Error {ex}")
            return False