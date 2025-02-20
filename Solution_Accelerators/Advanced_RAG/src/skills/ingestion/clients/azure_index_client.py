from azure.search.documents.indexes import SearchIndexClient
from azure.identity import DefaultAzureCredential
from common.telemetry.app_logger import AppLogger

class AzureIndexClient():
    '''
    A client to interact with Azure AI Search Index.
    '''
    def __init__(
        self,
        search_endpoint: str,
        logger: AppLogger
    ) -> None:
        self.index_client = SearchIndexClient(
            endpoint=search_endpoint,
            credential=DefaultAzureCredential()
        )
        self.logger = logger

    async def validate_index_name(self, index_name: str) -> bool:
        try:
            self.index_client.get_index(index_name)
            return True
        except Exception as ex:
            self.logger.error(f"Failed to validate index name.\nError {ex}")
            return False