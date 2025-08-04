from datetime import datetime, timezone

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.search.documents.aio import SearchClient
from azure.search.documents.models import QueryType, VectorizedQuery
from openai import AsyncAzureOpenAI

from common.telemetry.app_logger import AppLogger

SEMANTIC_CONFIGURATION_NAME = "market-research-semantic-configuration"
VECTOR_FIELD_NAMES = ["query_vector", "report_content_vector"]

class AzureAISearchHelper:
    """
    Helper class for interacting with Azure AI Search.
    This class provides methods to index documents and perform searches
    using hybrid and semantic search capabilities.

    Attributes:
        endpoint (str): The Azure AI Search service endpoint.
        index_name (str): The name of the search index to use.
        openai_endpoint (str): The endpoint for Azure OpenAI service.
        embeddings_deployment_name (str): The name of the OpenAI deployment for embeddings.
        api_version (str): The API version for Azure OpenAI.
    """
    def __init__(
        self,
        logger: AppLogger,
        endpoint: str,
        index_name: str,
        openai_endpoint: str,
        embeddings_deployment_name: str,
        api_version: str
    ):
        self.logger = logger
        self.embeddings_deployment_name = embeddings_deployment_name

        self.client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=DefaultAzureCredential()
        )

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )

        self.openai_client = AsyncAzureOpenAI(
            azure_endpoint=openai_endpoint,
            azure_ad_token_provider=token_provider,
            api_version=api_version,
        )

    async def get_embeddings(self, text: str) -> list:
        """
        Generate an embedding for the given text using Azure OpenAI.
        """
        response = await self.openai_client.embeddings.create(
            model=self.embeddings_deployment_name,
            input=[text]
        )
        return response.data[0].embedding

    async def save_report(self, generated_report: str, persona: str, report_level: str) -> bool:
        """
        Indexes (uploads/updates) documents to the Azure AI Search index.
        Each document should match the index schema.
        """
        self.logger.info("Saving report to Azure AI Search index.")

        try:
            # Format datetime as ISO 8601 string (UTC)
            now = datetime.now(timezone.utc)
            datetime_str = now.isoformat()

            report_content_vector = await self.get_embeddings(generated_report)
            document = [
                {
                    "id": f"{persona.replace(" ", "")}-{report_level}-{now.strftime("%Y-%m-%d_%H-%M-%S")}",
                    "report_content": generated_report,
                    "report_content_vector": report_content_vector,
                    "persona": persona,
                    "report_level": report_level,
                    "created_at": datetime_str
                }
            ]

            result = await self.client.upload_documents(documents=document)
            if not all([r.succeeded for r in result]):
                self.logger.error(f"Failed to upload document to Azure AI Search index: {result}")
                return False

            self.logger.info("Report saved successfully to Azure AI Search index.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save report to Azure AI Search index: {e}")
            return False

    async def search(self, query: str, top: int = 3, semantic: bool = True) -> list[dict]:
        """
        Performs a hybrid+semantic search against the index using the query.
        Generates the query vector embedding internally.
        """
        self.logger.info(f"Searching Azure AI Search index for query: {query}")

        # Generate query vector embedding
        query_vector = await self.get_embeddings(query)

        vector_queries = [
            VectorizedQuery(vector=query_vector,
                            fields=v,
                            k_nearest_neighbors=10) for v in VECTOR_FIELD_NAMES]

        results = await self.client.search(
            search_text=query,
            top=top,
            query_type=QueryType.SEMANTIC if semantic else QueryType.SIMPLE,
            semantic_configuration_name=SEMANTIC_CONFIGURATION_NAME if semantic else None,
            vector_queries=vector_queries
        )

        filtered_results = []
        async for result in results:
            filtered_result = {k: v for k, v in result.items() if not k.startswith("@search")}
            filtered_results.append(filtered_result)

        self.logger.info(f"Search result count: {len(filtered_results)}")
        return filtered_results

