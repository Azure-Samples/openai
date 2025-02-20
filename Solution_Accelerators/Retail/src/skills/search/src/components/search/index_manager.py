import os

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from typing import Dict

from common.clients.openai.openai_client import AzureOpenAIClient
from common.telemetry.app_logger import AppLogger
from components.shared.errors import InvalidConfigError
from components.search.index_search import SearchIndex
from components.models.config_models import SearchSkillConfig, IndexApplicationType


class SearchIndexManager:
    index_client: SearchIndexClient = None

    image_index = ""
    index_collection: Dict[str, SearchIndex] = {}

    def __init__(self, config: SearchSkillConfig, search_endpoint: str, openai_client: AzureOpenAIClient, embeddings_deployment: str, logger: AppLogger) -> None:
        self.configuration = config
        self.search_endpoint = search_endpoint
        self.openai_client = openai_client
        self.embeddings_deployment = embeddings_deployment
        self.logger = logger

        self._validate_indexes()

    def _validate_indexes(self):
        image_description_indexes = list()

        for index in self.configuration.config:           
            # 1- Index and Fields of index in config must exist in the Index definition - validation inside CSI class
            self.index_collection[index.index_name] = SearchIndex(
                name=index.index_name,
                search_endpoint=self.search_endpoint,
                openai_client=self.openai_client,
                embeddings_deployment=self.embeddings_deployment,
                select_fields=index.select_fields,
                vector_config=index.vector_configs,
                search_type=index.search_type,
                semantic_config=index.semantic_config,
                logger=self.logger
            )

            # 2- Storing productImage index
            if index.index_application == IndexApplicationType.image_description_search:
                image_description_indexes.append(index.index_name)


        if len(image_description_indexes) == 0:
            raise InvalidConfigError("At least 1 index must be used for image_description_search. Fix configuration")
        
        if len(image_description_indexes) > 1:
            raise InvalidConfigError("Only 1 index can be used for image_description_search. Fix configuration")
        
        # Storing product image index for reference
        self.image_index = image_description_indexes[0]

    def get_specific_index(self, index_name: str) -> SearchIndex | None:
        return self.index_collection.get(index_name, None)

    def get_product_image_index(self) -> SearchIndex | None:
        return self.get_specific_index(self.image_index)

    def get_index_client(self):
        if self.index_client == None:
            self.index_client = SearchIndexClient(
                endpoint=self.search_endpoint,
                credential=DefaultAzureCredential()
            )

        return self.index_client
